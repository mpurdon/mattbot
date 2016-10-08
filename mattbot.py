# -*- coding: UTF-8 -*-
"""
Implementation of the mattbot

"""

import os
import requests
import sys
import time

from slackclient import SlackClient

MATTBOT_ID = os.environ.get('MATTBOT_ID')
MATTBOT_TOKEN = os.environ.get('MATTBOT_TOKEN')

AT_MATTBOT = '<@{}>'.format(MATTBOT_ID)
READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from firehose

slack_client = None
slack_users = None
slack_channels = None
slack_ims = None


def handle_hello_command(channel, user, value):
    """

    :param channel:
    :param value:

    :return:
    """
    response = 'Hello, {}!'.format(slack_users[user])
    slack_client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)


def handle_bizzfuzz_command(channel, user, value):
    """

    :param channel:
    :param value:

    :return:
    """
    response = ''

    try:
        response = ''
        number = int(value.strip())
        if number % 15 == 0:
            response = 'BizzFuzz'
        elif number % 3 == 0:
            response = 'Bizz'
        elif number % 5 == 0:
            response = 'Fuzz'
        else:
            response = number
    except ValueError:
        response = 'Please privide a number, "{}" is not valid.'.format(value)
    finally:
        slack_client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)


def handle_command(channel, user, bot_command):
    """
    Receives commands directed at the bot and determines if they
    are valid commands. If so, then acts on the commands. If not,
    returns back what it needs for clarification.

    """
    print('>> Handling command {} from channel {}'.format(bot_command, channel))

    command_type, _, parameters = bot_command.partition(' ')
    command_handler = 'handle_{}_command'.format(command_type)
    current_module = sys.modules[__name__]

    try:
        handler = getattr(current_module, command_handler)
        return handler(channel, user, parameters)
    except AttributeError:
        response = 'Not sure what you mean.'
        slack_client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)


def handle_deploy_log(file):
    """
    Handle a log file

    """
    start_log = '#### RUNNING MIGRATIONS'
    end_log = ''

    recipients = ['mpurdon']

    url = file.get('url_private ')
    file_contents = requests.get(url)

    found_migrations = False
    log_content = []

    for line in file_contents:
        if not found_migrations:
            if start_log in line:
                found_migrations = True
            else:
                continue


def handle_file(channel, user, file_data):
    """
    Handle a file upload

    """
    print('>> Handling file {} from channel {}'.format(file_data['name'], channel))

    if channel == 'foo':
        return handle_deploy_log(file_data)

    # slack_client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)


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

        if 'file' in output and channel_name == 'mpurdon':
            return handle_file(channel_name, user, output['file'])

        text = output.get('text', '')

        if AT_MATTBOT in text:
            bot_command = text.split(AT_MATTBOT)[1].strip().lower()
            return handle_command(channel, user, bot_command)

        if channel in slack_ims and user != MATTBOT_ID:
            return handle_command(channel, user, text)

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


if __name__ == "__main__":

    slack_client = SlackClient(MATTBOT_TOKEN)

    if not slack_client.rtm_connect():
        print("Connection failed. Invalid Slack token or bot ID?")
        sys.exit()

    print('MattBot connected and running!')

    slack_users = get_users()
    print ('\n'.join([k+':'+v for k, v in slack_users.items()]))
    slack_channels = get_channels()
    print ('\n'.join([k + ':' + v for k, v in slack_channels.items()]))
    slack_ims = get_ims()
    print ('\n'.join([k + ':' + v for k, v in slack_ims.items()]))

    while True:
        parse_slack_output(slack_client.rtm_read())
        time.sleep(READ_WEBSOCKET_DELAY)
