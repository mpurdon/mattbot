# -*- coding: utf-8 -*-
"""
Commands the mattbot understands

"""


class Command(object):
    """

    """
    client = None

    def __init__(self, client, users, channels, ims):
        self.client = client
        self.users = users
        self.channels = channels
        self.ims = ims

    def run(self, channel, user, value):
        """
        Perform the actions of this command

        :param channel:
        :param user:
        :param value:
        """
        raise NotImplementedError('You must define a run method')


class HelloCommand(Command):
    """
    Handle "hello"

    """
    def run(self, channel, user, value):
        """
        Perform the action of this command

        :param channel:
        :param user:
        :param value:
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
            response = 'Please privide a number, "{}" is not valid.'.format(value)
        finally:
            self.client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)
