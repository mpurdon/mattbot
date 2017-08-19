"""
Commands specific to the bot

"""
import random
import re

from commands import badwords
from commands.base import Command, CommandResult


class HelloCommand(Command):
    """
    Handle "hello"

    """

    def run(self, parameters: str) -> bool:
        """

        Args:
            parameters: The command payload

        Returns:
            The CommandResult

        """
        response = f'Hello, {self.user_name}!'
        self.post_message(response)
        return CommandResult(success=True, message=response)


class BizzfuzzCommand(Command):
    """
    Handle "bizzfuzz"

    """

    def run(self, parameters: str) -> bool:
        """

        Args:
            parameters: The command payload

        Returns:
            The CommandResult

        """
        response = ''

        try:
            response = ''
            number = int(parameters.strip())
            if number % 15 == 0:
                response = 'BizzFuzz'
            elif number % 3 == 0:
                response = 'Bizz'
            elif number % 5 == 0:
                response = 'Fuzz'
            else:
                response = number
        except ValueError:
            response = f'{self.user_name}, please provide a number, "{parameters}" is not valid.'
        finally:
            self.post_message(response)

        return CommandResult(success=True, message=response)


class Magic8Command(Command):
    """
    Perform a magic 8 ball response

    """

    def run(self, parameters: str) -> bool:
        """

        Args:
            parameters: The command payload

        Returns:
            The CommandResult

        """
        options = ['Yes', 'Maybe', 'No', 'I do not know', 'Try again later', 'How should I know?']
        selected = random.choice(options)
        response = 'Magic 8-ball says....{}.'.format(selected)
        self.post_message(response)

        return CommandResult(success=True, message=response)


class WhoCommand(Command):
    """


    """

    def run(self, parameters: str) -> bool:
        """

        Args:
            parameters: The command payload

        Returns:
            The CommandResult

        """
        noun = random.choice(badwords.nouns)
        verb = random.choice(badwords.verbs)
        adjective = random.choice(badwords.adjectives)

        parameters = parameters.replace('?', '')

        pattern = re.compile('<@[A-Z0-9]+>')
        matches = re.search(pattern, parameters)
        subject_verb = 'is'

        try:
            if matches:
                target = matches.group()
            elif parameters[-2:] in (' i', ' I'):
                target = 'You'
                subject_verb = 'are'
            elif parameters[-4:] in (' you', ' You'):
                target = 'I'
                subject_verb = 'am'
            else:
                _, target = parameters.split(None, 1)
                # self.bot.get_user_name(user)

            indefinite_article = 'a'
            if adjective[0].lower() in ('a', 'e', 'i', 'o', 'u'):
                indefinite_article = 'an'

            response = f'{target} {subject_verb} {indefinite_article} {adjective} {noun}, that likes to {verb}'
        except ValueError:
            response = f'I need a name to tell you who someone is.'

        self.post_message(response)

        return CommandResult(success=True, message=response)
