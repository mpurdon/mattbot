# -*- coding: UTF-8 -*-
"""
Get the ID of mattbot

"""
from __future__ import unicode_literals, print_function

import os

from slackclient import SlackClient

BOT_NAME = 'mattbot'
MATTBOT_TOKEN = os.environ.get('MATTBOT_TOKEN')

slack_client = SlackClient(MATTBOT_TOKEN)

if __name__ == '__main__':

    bot_id = None

    api_call = slack_client.api_call('users.list')

    if not api_call.get('ok'):
        print('API call failed: {}'.format(api_call.get('error')))
        exit()

    # retrieve all users so we can find our bot
    users = api_call.get('members')
    for user in users:
        user_id = user.get('id')
        user_name = user.get('name', None)

        print('-- {}'.format(user_name))

        if user_name == BOT_NAME:
            bot_id = user_id

    if not bot_id:
        print('Could not find bot user with the name {}'.format(BOT_NAME))
        exit()

    print('Bot ID for "{}" is "{}"'.format(BOT_NAME, bot_id))
