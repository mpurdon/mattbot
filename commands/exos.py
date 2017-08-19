"""
Commands specific to Exos

"""
import logging
import os
import requests

from commands.base import Command, CommandResult
from tempfile import NamedTemporaryFile

logger = logging.getLogger(__name__)


class HandleFileCommand(Command):
    """
    Handle "hello"

    """
    def run(self, parameters: str):
        """
        Perform the action of this command

        Args:
            parameters:

        Returns:

        """
        response = f'Hello, {self.user_name}!'
        self.post_message(response)
        return CommandResult(success=True, message=response)

    def check_deploy_log(self, lines):
        """
        Check for error key words or fake migration phrases

        Args:
            lines (list): The lines from the log file

        Returns:
            tuple:

        """
        error_words = [
            'Error',
            'Traceback'
        ]

        fake_phrases = [
            "Table 'bearprofile_fitbitactivitynotification' already exists"
        ]

        has_errors = False
        needs_fake = False

        for line in lines:
            if any(error_word in line for error_word in error_words):
                has_errors = True

            if any(fake_phrase in line for fake_phrase in fake_phrases):
                needs_fake = True

        return has_errors, needs_fake

    def download_file(self, url):
        """

        Args:
            url: The URL to download the file from

        """
        logger.debug('Getting file contents from "%s"', url)

        session = requests.Session()
        session.headers['Authorization'] = f'Bearer {self.bot.slack_token}'
        response = session.get(url, stream=True)

        if response.status_code != 200:
            logger.error('Could not download file from %s', url)
            return None

        with NamedTemporaryFile(delete=False) as log_file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    log_file.write(chunk)

            logger.debug('Saved log to %s', log_file.name)

            return log_file.name

    def handle_deploy_log(self, channel, file):
        """
        Handle a log file

        """
        start_log = '#### RUNNING MIGRATIONS'
        end_log = '#### DONE'

        url = file.get('url_private_download')

        file_name = self.download_file(url)

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

        has_errors, needs_fake = self.check_deploy_log(log_content)

        message = 'I could not find any issues in the {} file, check the snippet.'.format(file['name'])

        if has_errors:
            message = 'I found an issue in the {} file, check the snippet.'.format(file['name'])

        if needs_fake:
            message = 'The {} file is clean but I think we need to run the fake.'.format(file['name'])

        recipients = ['@mpurdon', ]
        recipient_channels = ','.join(recipients)

        snippet_file_name = 'snippet.{}'.format(file['name'])

        content = ''.join(log_content)

        print('Sending snippet {} to {}'.format(snippet_file_name, recipient_channels))
        api_response = self.bot.slack_client.api_call('files.upload',
                                                      channels=recipient_channels,
                                                      content=content,
                                                      initial_comment=message,
                                                      filetype='text',
                                                      filename=snippet_file_name)

        if not api_response.get('ok', False):
            message = 'Sorry, I was not able to send the snippet due to {api_response.get("error", "an error")}.'
            self.post_message(message)

        # Reply to the original channel with the message
        self.post_message(message)

    def handle_file(self, file_data):
        """
        Handle a file upload

        """
        if self.user == self.bot.slack_user_id:
            return

        file_name = file_data['name']

        if file_name.endswith('deploy.log'):
            response = f'Handling file {file_name} from channel {self.channel_name} by {self.user_name}'
            if self.handle_deploy_log(self.channel, file_data):
                return CommandResult(success=True, message=response)

            return CommandResult(success=False, message=f'Could not handle the file {file_name}')

        response = 'I have nothing to say about that file.'
        self.post_message(response)
