from alexa_skill_kit import AlexaSkillKit
from forismatic import Forismatic

ask = AlexaSkillKit()

@ask.on_launch
def launch():
    return ask.success(message='Hello, welcome to Random Quotes skill! What quote do you want me to tell you? You could say Hey tell me a random quote.')

@ask.on_intent
def intent():
    return ask.success(message='I got it!', card_title='Card title shows up on Alexa app', card_content='content')

@ask.on_help
def help():
    return ask.success(message='You could say Hey tell me a random quote.', message_reprompt='This message will play again after a while')

@ask.on_session_ended
def session_ended():
    return ask.success(message='good bye!')

@ask.on_stop
def stop():
    return ask.success(message='good bye!')

@ask.on_trigger
def main(event, context):
# This is the main entry of your Lambda function

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
    # fake event for local development. Look into tests/data/*.json for fake json files
    event = {}
    main(event=event, context={})
