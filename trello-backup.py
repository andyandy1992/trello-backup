#!/usr/bin/python -u

import ConfigParser
import os, sys
import json
import requests
import time
import io
import shutil

configFile = 'trello-backup.config'
configFile = os.path.join(os.path.abspath(os.path.dirname(__file__)), configFile)
now = time.strftime("%Y%m%d-%H%M")


def main():
    if os.path.isfile(configFile):
        config = ConfigParser.RawConfigParser()
        config.read(configFile)
    else:
        sys.exit('Config file "{0}" does not exist.'.format(configFile))

    API_KEY = config.get('Credentials', 'API_KEY')
    TOKEN = config.get('Credentials', 'TOKEN')

    API_URL = config.get('Paths', 'API_URL')
    BASE_DIRECTORY = config.get('Paths', 'BASE_DIRECTORY')
    OUTPUT_DIRECTORY = BASE_DIRECTORY + u'/' + now

    TOKEN_EXPIRATION = config.get('Options', 'TOKEN_EXPIRATION')
    APP_NAME = config.get('Options', 'APP_NAME')
    ORGANIZATION_ID = config.get('Options', 'ORGANIZATION_ID')
    PRETTY_PRINT = config.get('Options', 'PRETTY_PRINT') == 'yes'
    NUM_BACKUPS = config.get('Options', 'NUM_BACKUPS')

    if not API_KEY:
        print('You need an API key to run this app.')
        print('Visit this url: https://trello.com/app-key')
        API_KEY = raw_input('Then enter the API key here: ')
        print('\n[IMPORTANT] Make sure to add the key to the config file.\n')
        raw_input('Press enter to continue...\n')

    if not TOKEN:
        print('You need a token to run this app.')
        print("Visit this url: https://trello.com/1/authorize?response_type=token&key={0}&scope=read&expiration={1}&name={2}".format(API_KEY, TOKEN_EXPIRATION, APP_NAME))
        TOKEN = raw_input('Then enter the token here: ')
        print('\n[IMPORTANT] Make sure to add the token to the config file.\n')
        raw_input('Press enter to continue...\n')

    # Parameters to get list of boards
    boardsPayload = {
        'key':API_KEY,
        'token':TOKEN,
        'lists':'all',
    }
    # Parameters to get board contents
    boardPayload = {
        'key':API_KEY,
        'token':TOKEN,
        'lists':'all',
        'fields':'all',
        'actions':'all',
        'action_fields':'all',
        'actions_limit':'1000',
        'cards':'all',
        'card_fields':'all',
        'card_attachments':'true',
        'labels':'all',
        'lists':'all',
        'list_fields':'all',
        'members':'all',
        'member_fields':'all',
        'checklists':'all',
        'checklist_fields':'all',
        'organization':'false',
    }
    boards = requests.get(API_URL + "members/my/boards", data=boardsPayload)
    try:
        if len(boards.json()) <= 0:
            print('No boards found.')
            return
    except ValueError:
        print('Unable to access your boards. Check your key and token.')
        return

    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(OUTPUT_DIRECTORY)

    print("Backing up boards to {0}:".format(OUTPUT_DIRECTORY))

    for board in boards.json():
        if ORGANIZATION_ID and board["idOrganization"] != ORGANIZATION_ID:
            continue

        print(u"    - {0} ({1})".format(board["name"], board["id"]))
        boardContents = requests.get(API_URL + "boards/" + board["id"], data=boardPayload)
        with io.open(OUTPUT_DIRECTORY + u'/{0}'.format(board["name"].replace("/","-")) + '.json', 'w', encoding='utf8') as file:
            args = dict( sort_keys=True, indent=4) if PRETTY_PRINT else dict()
            data = json.dumps(boardContents.json(), ensure_ascii=False, **args)
            file.write(unicode(data))

    #Keep NUM_BACKUPS copies of the most recent backups
    if NUM_BACKUPS == "all":
        sys.exit(0)

    sorted_backups = sorted_ls(BASE_DIRECTORY)
    while len(sorted_backups) > int(NUM_BACKUPS):
        old_dir = sorted_backups.pop(0)
        shutil.rmtree(BASE_DIRECTORY + u'/' + old_dir)


def sorted_ls(dir):
    """ Return the contents of a given directory sorted by ascending modification time. """
    mtime = lambda f: os.stat(os.path.join(dir, f)).st_mtime
    return list(sorted(os.listdir(dir), key=mtime))


if __name__ == '__main__':
    main()
