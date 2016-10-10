# -*- coding: utf-8 -*-
"""
Commands the mattbot understands

"""


class Command(object):
    """

    """
    client = None

    def __init__(self, client, users, channels, ims):
        """
        Initialize the command

        Args:
            client:
            users:
            channels:
            ims:
        """
        self.settings = {
            'check_logs': None
        }
        self.client = client
        self.users = users
        self.channels = channels
        self.ims = ims

    def run(self, channel, user, value):
        """

        Args:
            channel:
            user:
            value:

        Returns:

        """
        raise NotImplementedError('You must define a run method')


class HelloCommand(Command):
    """
    Handle "hello"

    """
    def run(self, channel, user, value):
        """
        Perform the action of this command

        Args:
            channel:
            user:
            value:

        Returns:

        """
        response = 'Hello, {}!'.format(self.users[user])
        self.client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)


class BizzfuzzCommand(Command):
    """
    Handle "bizzfuzz"

    """

    def run(self, channel, user, value):
        """
        Perform the action of this command

        :param channel:
        :param user:
        :param value:
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
            response = '{}, please provide a number, "{}" is not valid.'.format(self.users[user], value)
        finally:
            self.client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)


class SetCommand(Command):
    """
    Update a command setting

    """
    def run(self, channel, user, value):
        """

        Args:
            channel:
            user:
            value:

        Returns:

        """
        setting, _, setting_value = value.partition(' ')
        self.settings[setting] = setting_value
        response = 'Okay {}, setting {} to {}'.format(self.users[user], setting, setting_value)
        self.client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)


class JoinCommand(Command):
    """
    Tell the bot to join a channel

    """
    def run(self, channel, user, value):
        """

        Args:
            channel:
            user:
            value:

        Returns:

        """
        api_response = self.client.api_call('channels.join', channel=value)
        if not api_response.get('ok'):
            response = 'Sorry, {}, I could not join {} due to {}.'.format(self.users[user], value, api_response.get('error', 'an error'))
            return self.client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)

        if api_response.get('already_in_channel', False):
            response = 'But {}, I am already in {}'.format(self.users[user], value)
            return self.client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)

        new_channel_info = api_response['channel']
        new_channel_id = new_channel_info['id']
        response = 'Okay {}, I am here now.'.format(self.users[user])
        self.client.api_call('chat.postMessage', channel=new_channel_id, text=response, as_user=True)


class LeaveCommand(Command):
    """
    Tell the bot to join a channel

    """
    def run(self, channel, user, value):
        """

        Args:
            channel:
            user:
            value:

        Returns:

        """
        response = 'Okay {}, I am leaving {}.'.format(self.users[user], self.channels[channel])
        self.client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)

        api_response = self.client.api_call('channels.leave', channel=channel)
        if not api_response.egt('ok', False):
            response = 'Sorry, {}, I could not leave {} due to {}.'.format(self.users[user], self.channels[channel], api_response.get('error', 'an error'))
            return self.client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)

