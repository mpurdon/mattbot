"""
Commands specific to the bot

"""
import logging

from commands.base import Command, CommandResult

logger = logging.getLogger(__name__)


class DieCommand(Command):
    """
    Die on command

    """
    def run(self, parameters: str) -> bool:
        """

        Args:
            parameters: The command payload

        Returns:
            The CommandResult

        """
        setting, _, setting_parameters = parameters.partition(' ')
        self.settings[setting] = setting_parameters
        response = f'Okay {self.user_name}, I am going to die.'
        self.post_message(response)
        self.bot.die()

        return CommandResult(success=True, message=response)


class SetCommand(Command):
    """
    Update a command setting

    """
    def run(self, parameters: str) -> bool:
        """

        Args:
            parameters:      The command payload

        Returns:
            The CommandResult

        """
        setting, _, setting_parameters = parameters.partition(' ')
        self.settings[setting] = setting_parameters
        response = f'Okay {self.user_name}, setting {setting} to {setting_parameters}'
        self.post_message(response)

        return CommandResult(success=True, message=response)


class JoinCommand(Command):
    """
    Tell the bot to join a channel

    """
    def run(self, parameters: str) -> bool:
        """

        Args:
            parameters: The command payload

        Returns:
            The CommandResult

        """
        api_response = self.call_api('channels.join', channel=parameters)
        if not api_response.get('ok'):
            error = api_response.get("error", "an error")
            response = f'Sorry, {self.user_name}, I could not join {parameters} due to {error}.'
            self.post_message(response)
            return CommandResult(success=True, message=response)

        if api_response.get('already_in_channel', False):
            response = f'But {self.user_name}, I am already in {parameters}'
            self.post_message(response)
            return CommandResult(success=True, message=response)

        new_channel_info = api_response['channel']
        new_channel_id = new_channel_info['id']
        response = f'Okay {self.user_name}, I am here now.'
        self.post_message(response)
        return CommandResult(success=True, message=response)


class LeaveCommand(Command):
    """
    Tell the bot to leave a channel

    """
    def run(self, parameters: str) -> bool:
        """

        Args:
            parameters: The command payload

        Returns:
            The CommandResult

        """
        response = f'Okay {self.user_name}, I am leaving {self.channel_name}.'
        self.post_message(response)

        api_response = self.call_api('channels.leave')
        if not api_response.get('ok', False):
            error = api_response.get("error", "an error")
            response = f'Sorry, {self.user_name}, I could not leave {self.channel_name} due to {error}.'
            self.post_message(response)
            return CommandResult(success=False, message=response)

        return CommandResult(success=True, message=f'Left channel {self.channel_name}')


class ListenCommand(Command):
    """
    Tell the bot to listen to the current channel

    """
    def run(self, parameters: str) -> bool:
        """

        Args:
            parameters: The command payload

        Returns:
            The CommandResult

        """
        response = f'Okay {self.user_name}, listening for events in {self.channel_name}.'
        self.post_message(response)

        return CommandResult(success=True, message=response)


class IgnoreCommand(Command):
    """
    Tell the bot to ignore commands in this channel

    """
    def run(self, parameters: str) -> bool:
        """

        Args:
            parameters: The command payload

        Returns:
            The CommandResult

        """
        response = f'Okay {self.user_name}, not listening for events in {self.channel_name}.'
        self.post_message(response)

        return CommandResult(success=True, message=response)
