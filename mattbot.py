# -*- coding: UTF-8 -*-
"""
Implementation of the mattbot

"""
import commands
import os
import requests
import sys
import time

from slackclient import SlackClient
from tempfile import NamedTemporaryFile

MATTBOT_NAME = 'mattbot'
MATTBOT_TOKEN = None

READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from fire hose

slack_client = None
slack_users = None
slack_channels = None
slack_ims = None


def handle_command(channel, user, bot_command):
    """
    Receives commands directed at the bot and determines if they
    are valid commands. If so, then acts on the commands. If not,
    returns back what it needs for clarification.

    """
    print('>> Handling command {} from channel {}'.format(bot_command, channel))

    command_type, _, parameters = bot_command.partition(' ')
    command_class = '{}Command'.format(command_type.capitalize())

    try:
        handler_class = getattr(commands, command_class)
        handler = handler_class(slack_client, slack_users, slack_channels, slack_ims)
        return handler.run(channel, user, parameters)
    except AttributeError:
        response = 'Not sure what you mean.'
        slack_client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)


def check_deploy_errors(lines):
    """

    Args:
        lines:

    Returns:

    """
    for line in lines:
        if 'Error' in line or 'Traceback' in line:
            return True

    return False


def download_file(url):
    """

    Args:
        url:
    """
    print('Getting file contents from "{}"'.format(url))

    session = requests.Session()
    session.headers['Authorization'] = 'Bearer {}'.format(MATTBOT_TOKEN)
    response = session.get(url, stream=True)

    if response.status_code != 200:
        print('Could not download file from {}'.format(url))
        return None

    with NamedTemporaryFile(delete=False) as log_file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                log_file.write(chunk)

        print('Saved log to {file.name}'.format(file=log_file))
        return log_file.name


def handle_deploy_log(channel, file):
    """
    Handle a log file

    """
    start_log = '#### RUNNING MIGRATIONS'
    end_log = '#### DONE'

    print(file)
    url = file.get('url_private_download')
    # url = file.get('permalink_public')

    file_name = download_file(url)

    if file_name is None:
        return None

    found_migrations = False
    log_content = []

    with open(file_name) as log:
        for line in log:
            if not found_migrations:
                if start_log in line:
                    print('Found the start of the log')
                    found_migrations = True
                else:
                    continue

            log_content.append(line)

            if found_migrations and end_log in line:
                print('Found the end of the log')
                break

    # Nuke the log file
    os.unlink(file_name)

    has_errors = check_deploy_errors(log_content)

    # recipients = ['robosung', 'mpurdon']
    recipients = ['mpurdon', ]
    recipient_ids = [recipient_id for recipient_id, name in slack_users.items() if name in recipients]

    if has_errors:
        message = 'I found an issue in the {} file, check the snippet.'.format(file['name'])
    else:
        message = 'I could not find any issues in the {} file, check the snippet.'.format(file['name'])

    snippet_file_name = 'snippet.{}'.format(file['name'])

    user_ims = {v: k for k, v in slack_ims.items() if v in recipient_ids}

    content = ''.join(log_content)

    for recipient_id in recipient_ids:
        im_id = user_ims[recipient_id]

        print('Sending message to {} IM.'.format(slack_users[recipient_id]))
        slack_client.api_call('chat.postMessage', channel=recipient_id, text=message, as_user=True)

        print('Sending snippet {} to {}'.format(snippet_file_name, slack_users[recipient_id]))
        api_response = slack_client.api_call('files.upload',
                                             channel=im_id,
                                             content=content,
                                             filename=snippet_file_name,
                                             as_user=True)

        if not api_response.get('ok', False):
            message = 'Sorry {}, I was not able to send the snippet to you due to {}.'.format(slack_users[recipient_id],
                                                                                              api_response.get('error', 'an error'))
            slack_client.api_call('chat.postMessage', channel=recipient_id, text=message, as_user=True)


def handle_file(channel, user, file_data):
    """
    Handle a file upload

    """
    file_name = file_data['name']
    print('>> Handling file {} from channel {} by {}'.format(file_name, channel, user))

    # if channel == 'foo':
    if file_name.endswith('deploy.log'):
        return handle_deploy_log(channel, file_data)

    response = 'I have nothing to say about that file.'
    slack_client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
    The Slack Real Time Messaging API is an events firehose.
    this parsing function returns None unless a message is
    directed at the Bot, based on its ID.

    """
    if not slack_rtm_output:
        return None, None

    # print('Parsing slack message: {}'.format(slack_rtm_output))

    for output in slack_rtm_output:

        message_type = output.get('type', None)
        if message_type != 'message':
            # print('\t-- skipping type {}'.format(message_type))
            continue

        user = output.get('user')

        channel = output.get('channel')
        try:
            channel_name = slack_channels[channel]
        except KeyError:
            if channel in slack_ims:
                channel_name = 'private messages'

        if 'file' in output:
            return handle_file(channel_name, user, output['file'])

        text = output.get('text', '')

        if AT_MATTBOT in text:
            bot_command = text.split(AT_MATTBOT)[1].strip().lower()
            return handle_command(channel, user, bot_command)

        if channel in slack_ims and user != MATTBOT_ID:
            return handle_command(channel, user, text)

        if user != MATTBOT_ID:
            print('{user} says: "{message}" in {channel}'.format(user=slack_users[user],
                                                                 message=text,
                                                                 channel=channel_name))


def get_users():
    """

    :return:
    """
    slack_users = {}

    api_call = slack_client.api_call('users.list')
    if api_call.get('ok', False):
        # retrieve all users so we can find our bot
        users = api_call.get('members')
        for user in users:
            user_id = user.get('id')
            user_name = user.get('name', None)
            slack_users[user_id] = user_name

    return slack_users


def get_channels():
    """

    :return:
    """
    slack_channels = {}

    api_call = slack_client.api_call('channels.list')
    if api_call.get('ok', False):
        # retrieve all channels so we can find our bot
        channels = api_call.get('channels')
        for channel in channels:
            channel_id = channel.get('id')
            channel_name = channel.get('name', None)
            slack_channels[channel_id] = channel_name

    return slack_channels


def get_ims():
    """

    :return:
    """
    slack_ims = {}

    api_call = slack_client.api_call('im.list')
    if api_call.get('ok', False):
        # retrieve all channels so we can find our bot
        ims = api_call.get('ims')
        for im in ims:
            im_id = im.get('id')
            im_user = im.get('user', None)
            slack_ims[im_id] = im_user

    return slack_ims


def get_user_id(users, name):
    """
    Get the user id for th given username

    Args:
        users: dict
        name: string

    Returns:
        integer

    """
    for user_id, user_name in users.items():
        if user_name == name:
            return user_id

    return None


if __name__ == "__main__":

    MATTBOT_TOKEN = os.environ.get('MATTBOT_TOKEN')
    print('Attempting to connect with token: {}'.format(MATTBOT_TOKEN))
    slack_client = SlackClient(MATTBOT_TOKEN)

    if not slack_client.rtm_connect():
        print("Connection failed, invalid Slack token.")
        sys.exit()

    print('MattBot connected and running!')

    slack_users = get_users()
    print ('\n'.join([k+':'+v for k, v in slack_users.items()]))
    MATTBOT_ID = get_user_id(slack_users, MATTBOT_NAME)
    print('Bot id: {}'.format(MATTBOT_ID))
    AT_MATTBOT = '<@{}>'.format(MATTBOT_ID)

    slack_channels = get_channels()
    print('\nChannels')
    print ('\n'.join([k + ':' + v for k, v in slack_channels.items()]))

    slack_ims = get_ims()
    print ('\nIMs')
    print ('\n'.join([k + ':' + v for k, v in slack_ims.items()]))

    while True:
        parse_slack_output(slack_client.rtm_read())
        time.sleep(READ_WEBSOCKET_DELAY)
