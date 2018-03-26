import json
import boto3
import requests
import os
import yaml

from randomquotes import AlexaSkillKit
from randomquotes import Forismatic
from pathlib import Path

with Path.cwd().joinpath('randomquotes/script.yml').open() as f: script = yaml.load(f)

ask = AlexaSkillKit(app_id='amzn1.ask.skill.370ea4e5-efc0-4f4d-950c-41bfa48e00d0')

@ask.on_launch
def launch():
    return ask.success(message=script['welcome'])

@ask.on_intent
def intent():
    fori = Forismatic()
    q = fori.get_quote()
    answer = script['answer_speech'].format(quote=q.quote,author=q.author)
    card_title = script['answer_card_title'].format(author=q.author)
    card_content = script['answer_card_content'].format(quote=q.quote,author=q.author)

    return ask.success(message=answer,message_reprompt=script['answer_repeat'], card_title=card_title, card_content=card_content)

@ask.on_help
def help():
    return ask.success(message=script['help'], message_reprompt=script['help_repeat'])

@ask.on_session_ended
def session_ended():
    return ask.success(message=script['bye'])

@ask.on_stop
def stop():
    return ask.success(message=script['bye'])

@ask.on_trigger
def main(event, context):
# This is the main entry of your Lambda function
    print(event['request'])
    if ask.launch():
        return launch()
    elif ask.intent():
        return intent()
    elif ask.session_ended():
        return session_ended()
    elif ask.help():
        return help()
    elif ask.stop() or ask.cancel():
        return stop()

if __name__ == '__main__':
    # fake event for local development. Look into test/data/*.json for fake json files
    test_file = 'test/launch.json'
    with open(test_file, 'r') as f:
        event = json.load(f)
    main(event=event, context={})
