"""
Commands specific to the bot

"""
import logging

from commands.base import Command, CommandResult

logger = logging.getLogger(__name__)


class TestCommand(Command):
    """
    Perform some test action in the current channel

    """
    def run(self, parameters: str) -> bool:
        """

        Args:
            parameters: The command payload

        Returns:
            The CommandResult

        """
        response = f'Okay {self.user_name}, I going to try uploading a snippet.'
        self.client.api_call('chat.postMessage', channel=self.channel, text=response, as_user=True)

        recipients = ['@mpurdon', ]
        # recipient_ids = [recipient_id for recipient_id, name in self.users.items() if name in recipients]

        snippet_file_name = f'snippet.{"foo"}.log'

        # user_ims = {v: k for k, v in self.ims.items() if v in recipient_ids}

        content = 'This is the content of a really cool snippet'

        # for recipient_id in recipient_ids:
        #     im_id = user_ims[recipient_id]

        recipients = ','.join(recipients)
        logger.debug('Sending snippet % to %', snippet_file_name, recipients)
        api_response = self.client.api_call('files.upload',
                                            channels=recipients,
                                            filename=snippet_file_name,
                                            filetype='text',
                                            content=content,
                                            initial_comment='I could not find a problem with the log.')

        logger.debug('Got response: %', api_response)

        if not api_response.get('ok', False):
            error = api_response.get("error", "an error")
            message = f'Sorry {self.user_name}, I was not able to send the snippet due to {error}.'
            self.client.api_call('chat.postMessage', channel=self.channel, text=message, as_user=True)
            return CommandResult(success=False, message=message)

        return CommandResult(success=False, message='Saved snippet.')
