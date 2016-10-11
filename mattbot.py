# -*- coding: UTF-8 -*-
"""
Implementation of the mattbot

"""
import commands
import config
import os
import requests
import sys
import time

from slackclient import SlackClient
from tempfile import NamedTemporaryFile


class Message(object):
    """
    A message in the RTM

    """
    def __init__(self, bot, content):
        """
        Represents a message from the Slack RTM firehose

        """
        message_type = content.get('type', None)
        if message_type != 'message':
            raise AttributeError('{} is not a valid message type.'.format(message_type))

        user = content.get('user')

        channel = content.get('channel')
        try:
            channel_name = slack_channels[channel]
        except KeyError:
            if channel in slack_ims:
                channel_name = 'private messages'

        if 'file' in content:
            return handle_file(channel_name, user, content['file'])

        text = content.get('text', '')

        if AT_MATTBOT in text:
            bot_command = text.split(AT_MATTBOT)[1].strip().lower()
            return handle_command(channel, user, bot_command)

        if channel in slack_ims and user != MATTBOT_ID:
            return handle_command(channel, user, text)

        if user != MATTBOT_ID:
            print('{user} says: "{message}" in {channel}'.format(user=slack_users[user],
                                                                 message=text,
                                                                 channel=channel_name))


class MattBot(object):
    """
    The Slack Bot

    """
    def __init__(self, config):
        """

        Args:
            config:
        """
        self.name = config.BOT_NAME
        self.read_websocket_delay = config.READ_WEBSOCKET_DELAY

        self.token = os.environ.get(config.BOT_ENV_TOKEN)
        print('Attempting to connect with token: {}'.format(self.token))
        self.slack = SlackClient(self.token)

        if not self.slack.rtm_connect():
            print('Connection failed, invalid Slack token.')
            sys.exit()

        self.fetch_users()
        self.fetch_channels()
        self.fetch_ims()

        self.bot_id = self.user_names_ids[self.name]
        self.bot_mentioned = '<@{}>'.format(self.bot_id)

        print('MattBot connected and running!')

    def run(self):
        """

        Returns:

        """
        while True:
            rtm_messages = self.slack.rtm_read()
            for rtm_message in rtm_messages:
                try:
                    message = Message(self, rtm_message)
                    self.handle_message(message)
                except AttributeError as error:
                    print(str(error))

            time.sleep(self.read_websocket_delay)

    def handle_message(self, message):
        """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.

        """
        print('>> Handling message {} from channel {}'.format(message.content, channel))

        command_type, _, parameters = bot_command.partition(' ')
        command_class = '{}Command'.format(command_type.capitalize())

        try:
            handler_class = getattr(commands, command_class)
            handler = handler_class(slack_client, slack_users, slack_channels, slack_ims)
            return handler.run(channel, user, parameters)
        except AttributeError:
            response = 'Not sure what you mean.'
            slack_client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)

    def fetch_users(self):
        """

        """
        self.user_names_ids = {}
        self.user_ids_name = {}

        api_response = self.slack.api_call('users.list')
        if api_response.get('ok', False):
            users = api_response.get('members')
            for user in users:
                user_id = user.get('id')
                user_name = user.get('name')
                self.user_names_ids[user_name] = user_id
                self.user_ids_name[user_id] = user_name

    def fetch_channels(self):
        """

        """
        self.channel_names_ids = {}
        self.channel_ids_names = {}

        api_response = self.slack.api_call('channels.list')
        if api_response.get('ok', False):
            channels = api_response.get('channels')
            for channel in channels:
                channel_id = channel.get('id')
                channel_name = channel.get('name')
                self.channel_names_ids[channel_name] = channel_id
                self.channel_ids_names[channel_id] = channel_name

    def fetch_ims(self):
        """

        """
        self.im_names_ids = {}
        self.im_ids_names = {}

        api_response = self.slack.api_call('im.list')
        if api_response.get('ok', False):
            # retrieve all channels so we can find our bot
            ims = api_response.get('ims')
            for im in ims:
                im_id = im.get('id')
                im_user = im.get('user')
                self.channel_names_ids[im_user] = im_id
                self.channel_ids_names[im_id] = im_user


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



if __name__ == "__main__":
    bot = MattBot(config.Configuration)
    bot.run()
