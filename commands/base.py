"""
Base Command classes

"""
import logging

from bot import MattBot
from collections import namedtuple

logger = logging.getLogger(__name__)


class CommandResult(namedtuple('CommandResult', ['success', 'message'])):
    """
    Represents a result and message.

    The string representation of this class returns the message and testing
    it against boolean returns the success.

    """
    def __str__(self):
        return str(self.message)

    def __bool__(self):
        return self.success


class Command:
    """
    Base command class

    """
    client = None
    channel = 'unknown'
    user = 'unknown'

    def __init__(self, bot: MattBot, channel: str, user: str) -> None:
        """
        Initialize the command

        Args:
            bot:    An instance of the MattBot
            channel:The channel the event took place in
            user:   The user who initiated the event

        """
        self.settings = {
            'check_logs': None
        }
        self.bot = bot
        self.channel = channel
        self.channel_name = self.bot.get_channel_name(channel)
        self.user = user
        self.user_name = self.bot.get_user_name(user)

    def call_api(self, endpoint: str, message: str = None, **parameters) -> dict:
        """
        Make an API call

        Args:
            endpoint:   The endpoint to communicate with
            message:    The message to send.
            parameters: Other parameters

        Returns:
            Whether or not the call was successful

        """
        return self.bot.slack_client.api_call(endpoint, text=message, channel=self.channel, as_user=True, **parameters)

    def post_message(self, message) -> dict:
        """
        Post a message

        Args:
            message:

        Returns:

        """
        return self.call_api(endpoint='chat.postMessage', message=message)

    def join_channel(self, channel: str) -> dict:
        """

        Args:
            channel: The channel to join

        """
        return self.bot.slack_client.api_call('channels.join', channel=channel)

    def run(self, parameters: str) -> bool:
        """

        Args:
            parameters: The content of the command

        """
        raise NotImplementedError('You must define a run method')
