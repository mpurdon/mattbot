# -*- coding: UTF-8 -*-
"""
Implementation of the mattbot

"""

import os
import sys
import time

from slackclient import SlackClient

MATTBOT_ID = os.environ.get('MATTBOT_ID')
SLACK_TOKEN = os.environ.get('SLACK_BOT_TOKEN')

# constants
AT_BOT = '<@{}>'.format(MATTBOT_ID)
EXAMPLE_COMMAND = "do"
READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from firehose

# instantiate Slack & Twilio clients
slack_client = SlackClient(SLACK_TOKEN)


def handle_command(bot_command, channel):
    """
    Receives commands directed at the bot and determines if they
    are valid commands. If so, then acts on the commands. If not,
    returns back what it needs for clarification.

    """
    print('>> Handling command {} from channel {}'.format(bot_command, channel))

    response = 'Not sure what you mean. Use the "' + EXAMPLE_COMMAND + '" command with numbers, delimited by spaces.'

    if command.startswith(EXAMPLE_COMMAND):
        response = 'Sure...write some more code then I can do that!'

    slack_client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
    The Slack Real Time Messaging API is an events firehose.
    this parsing function returns None unless a message is
    directed at the Bot, based on its ID.

    """
    if not slack_rtm_output:
        return None, None

    print('Parsing slack message: {}'.format(slack_rtm_output))

    for output in slack_rtm_output:
        if 'text' in output and AT_BOT in output['text']:
            bot_command = output['text'].split(AT_BOT)[1].strip().lower()
            return bot_command, output['channel']

    return None, None


if __name__ == "__main__":

    if not slack_client.rtm_connect():
        print("Connection failed. Invalid Slack token or bot ID?")
        sys.exit()

    print('MattBot connected and running!')

    while True:

        command, channel = parse_slack_output(slack_client.rtm_read())

        if command and channel:
            handle_command(command, channel)

        time.sleep(READ_WEBSOCKET_DELAY)
