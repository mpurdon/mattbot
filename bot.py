"""
Implementation of the mattbot

"""
import inspect
import logging
import os
import sys
import time
import typing

from slackclient import SlackClient

import commands

logger = logging.getLogger(__name__)

READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from fire hose


class MattBot:
    """
    The bot

    """
    name = 'mattbot'
    available_commands = None

    slack_client = None
    slack_user_id = None
    slack_users = None
    slack_channels = None
    slack_ims = None
    voice_engine = None
    living = True

    def __init__(self, token: str, name: str = None):
        """
        Initialize the bot


        """
        if name is not None:
            self.name = name

        self.slack_token = token
        self.connect()

    def connect(self):
        """

        """
        print(f'Attempting to connect with token: {self.slack_token}')
        self.slack_client = SlackClient(self.slack_token)

        if not self.slack_client.rtm_connect():
            print("Connection failed, invalid Slack token.")
            sys.exit()

        print('MattBot connected and running!')

        self.slack_users = self.get_users()
        print('\n'.join([k + ':' + v for k, v in self.slack_users.items()]))
        self.slack_user_id = self.get_user_id(self.slack_users, self.name)
        print(f'Bot id: {self.slack_user_id}')

        self.slack_channels = self.get_channels()
        print('\nChannels')
        print('\n'.join([k + ':' + v for k, v in self.slack_channels.items()]))

        self.slack_ims = self.get_ims()
        print('\nIMs')
        print('\n'.join([k + ':' + v for k, v in self.slack_ims.items()]))

        voice_engine = None
        # voice_engine = pyttsx.init()
        # voices = voice_engine.getProperty('voices')

    @property
    def at_name(self):
        """
        Get the at name of the bot.

        """
        return f'<@{self.slack_user_id}>'

    def die(self):
        """
        Stop execution of this bot.

        """
        self.living = False
        print('I have died.')

    def listen(self):
        """

        :return:
        """
        while self.living:
            self.parse_slack_output(self.slack_client.rtm_read(), self.voice_engine)
            time.sleep(READ_WEBSOCKET_DELAY)

    def parse_slack_output(self, slack_rtm_output, voice_engine):
        """
        The Slack Real Time Messaging API is an events fire hose.

        This parsing function returns None unless a message is directed at the
        Bot, based on its ID.

        """
        if not slack_rtm_output:
            return None, None

        # print(f'Parsing slack message: {slack_rtm_output}')

        for output in slack_rtm_output:

            message_type = output.get('type', None)
            if message_type != 'message':
                # print('\t-- skipping type {}'.format(message_type))
                continue

            user = output.get('user')

            if user == self.slack_user_id:
                continue

            print(f'Message from: {user}')
            channel = output.get('channel')
            channel_name = None

            try:
                channel_name = self.slack_channels[channel]
            except KeyError:
                if channel in self.slack_ims:
                    channel_name = 'private messages'

            if 'file' in output:
                return self.handle_command(channel, user, 'handle file')
                # return handle_file(channel_name, user, output['file'])

            text = output.get('text', '')

            if self.at_name in text:
                bot_command = text.split(self.at_name)[1].strip().lower()
                return self.handle_command(channel, user, bot_command)

            if channel in self.slack_ims:
                return self.handle_command(channel, user, text)

            # voice_engine.setProperty('voice', voices[0].id)  # changes the voice to Ivy
            # voice_engine.setProperty('voice', voices[1].id)  # changes the voice to Stuart

            try:
                message = f'{self.slack_users[user]} says: "{text}" in {channel_name}'
                # voice_engine.say(message)
                # voice_engine.runAndWait()
                print(message)
            except KeyError as error:
                print(f'Error "{error}" while processing "{text}"')
            except UnicodeEncodeError as error:
                print(f'Could not parse message: {error}')

    def get_command_class(self, command: str, channel: str, user: str):
        """
        Get a command class from a command name

        Args:
            command: The name of the command initiated.
            channel: The channel the command was initiated in.
            user:    The user that initiated the command.

        Returns: The class of the command to run

        """
        try:
            command_class = f'{command.capitalize()}Command'
            handler_class = getattr(commands, command_class)
            return handler_class(self, channel=channel, user=user)
        except AttributeError:
            logger.debug('Could not load the %s handler class.', command_class)
            return None

    def get_available_commands(self) -> list:
        """
        Get a list of commands

        """
        if self.available_commands:
            return self.available_commands

        self.available_commands = [command_name for command_name, command_class in inspect.getmembers(commands)
                                                if inspect.isclass(command_class)]

        return self.available_commands

    def handle_command(self, channel, user, bot_command):
        """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.

        """
        command_type, _, parameters = bot_command.partition(' ')

        logger.debug('Handling command %s from channel %s', command_type, channel)
        handler = self.get_command_class(command_type, channel, user)
        if handler is not None:
            return handler.run(parameters)

        available_commands = ', '.join(self.get_available_commands())
        logger.warning('unknown command %s, must be one of:%s', command_type, available_commands)
        response = f'Not sure what you mean. Available commands are: {available_commands}'
        self.slack_client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)

    def get_users(self) -> dict:
        """
        Get all users in the slack application

        """
        slack_users = {}

        api_call = self.slack_client.api_call('users.list')
        if api_call.get('ok', False):
            # retrieve all users so we can find our bot
            users = api_call.get('members')
            for user in users:
                user_id = user.get('id')
                user_name = user.get('name', None)
                slack_users[user_id] = user_name

        return slack_users

    def get_channels(self) -> dict:
        """
        Get all slack channels

        """
        slack_channels = {}

        api_call = self.slack_client.api_call('channels.list')
        if api_call.get('ok', False):
            # retrieve all channels so we can find our bot
            channels = api_call.get('channels')
            for channel in channels:
                channel_id = channel.get('id')
                channel_name = channel.get('name', None)
                slack_channels[channel_id] = channel_name

        return slack_channels

    def get_ims(self):
        """

        :return:
        """
        slack_ims = {}

        api_call = self.slack_client.api_call('im.list')
        if api_call.get('ok', False):
            # retrieve all channels so we can find our bot
            ims = api_call.get('ims')
            for im in ims:
                im_id = im.get('id')
                im_user = im.get('user', None)
                slack_ims[im_id] = im_user

        return slack_ims

    def get_user_id(self, users: dict, name: str) -> typing.Union[int, None]:
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

    def get_user_name(self, user_code):
        """
        Get a user name from a user code

        Args:
            user_code: The user code to look up
        """
        try:
            return self.slack_users[user_code]
        except KeyError:
            logger.error('Could not find a user with the code %s', user_code)

        return 'unknown user'

    def get_channel_name(self, channel_code):
        """
        Get a channel name from a channel code

        Args:
            channel_code: The channel code to look up
        """
        try:
            return self.slack_channels[channel_code]
        except KeyError:
            logger.warning('Could not find a channel with the code %s', channel_code)
            try:
                return self.slack_users[self.slack_ims[channel_code]]
            except KeyError:
                logger.error('Could not find an IM with the code %s', channel_code)

        return 'unknown channel'

if __name__ == "__main__":

    bot = MattBot(name='mattbot',
                  token=os.environ.get('MATTBOT_TOKEN'))
    bot.listen()
