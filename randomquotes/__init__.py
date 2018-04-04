import logging
import boto3
import json
import requests
import time
import aniso8601
import requests
import yaml
import sys
import os

from base64 import b64decode
from datetime import datetime
from pathlib import Path
from functools import wraps

class Quote(object):
    """
    Quote object, forming from given data

    """

    def __init__(self, data):
        # self.__quote = data['quoteText']
        self.__quote = bytes(data['quoteText'], "utf-8").decode("unicode_escape")
        self.__author = data['quoteAuthor']
        self.__sender_name = data['senderName']
        self.__sender_link = data['senderLink']
        self.__datetime = datetime.now()

    @property
    def quote(self):
        return self.__quote

    @property
    def author(self):
        return self.__author

    @property
    def sender_name(self):
        return self.__sender_name

    @property
    def sender_link(self):
        return self.__sender_link

    @property
    def __recieved_datetime(self):
        return self.__datetime


class Forismatic(object):
    """
    Manager for getting quotes using Forismatic API (default = 1.0)
    Supports POST & GET methods, russian & english quotes

    """

    def __init__(self, method="POST", api_url='http://api.forismatic.com/api/1.0/'):

        if method not in ["POST", "GET"]:
            raise Exception("Unknown method %s" % method)
        self.method = method
        self.api_url = api_url


    def get_quote(self, lang='en', key=None):
        '''
        Method for retrieve quote

        '''

        str_key = str(key)

        # Validation of input data
        if key:
            if len(str_key) > 6:
                raise Exception('Key max length is 6')

        if lang not in ['en', 'ru']:
            raise Exception('Unknown language: %s' % lang)

        headers = {
            'Cache-Control': "no-cache"
        }

        send_data = {
            'method': 'getQuote',
            'format': 'json',
            'lang': lang,
            'key': str_key if key else ""
        }

        if self.method == "POST":
            response = requests.request("POST", self.api_url, headers=headers, params=send_data)
        else:
            response = requests.request("GET", self.api_url, headers=headers, params=send_data)

        if response.status_code == 200:
            # Decoding JSON and fill Quote, if HTTP responce is OK
            try:
                return Quote(data=response.json())
            except:
                return Quote(
                    data={
                        "quoteText":"blank",
                        "quoteAuthor":"blank",
                        "senderName":"",
                        "senderLink":""
                        })
        else:
            return None

__version__ = '1.0.1'
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

kms = boto3.client('kms')
base_url = 'https://api.amazonalexa.com/v1'

class AlexaSkillKit:
    def __init__(self, app_id=None):
        self.app_id = app_id

    def init(self, event, script_path='randomquotes/script.yml'):
        self.event = event
        request = event['request']
        session = event['session']
        context = event['context']

        self.request_app_id = session['application']['applicationId']
        self.user_id = session['user']['userId']
        self.new_session = session['new']

        self.request_id = request['requestId']
        self.timestamp = request['timestamp']
        self.request_type = request['type']

        if 'intent' in request:
            self.intent_name = request['intent']['name']
            # self.slots = request['intent']['slots']
        else:
            self.intent_name = False
            # self.slots = False

        with Path.cwd().joinpath(script_path).open() as f:
            self.script = yaml.load(f)
            # print('script is ', self.script)

    def launch(self):
        return self.request_type == 'LaunchRequest'

    def intent(self):
        return self.request_type == 'IntentRequest'

    def session_ended(self):
        return self.request_type == 'SessionEndedRequest'

    def help(self):
        return self.intent_name and self.intent_name == 'AMAZON.HelpIntent'

    def stop(self):
        return self.intent_name and self.intent_name == 'AMAZON.StopIntent'

    def cancel(self):
        return self.intent_name and self.intent_name == 'AMAZON.CancelIntent'

    def on_trigger(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            self.init(event=args[0])
            valid = self._validate()
            if not valid:
                raise VerificationError('Failed validation.')
            return f(*args, **kwargs)

        return wrapper

    def on_intent(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapper

    def on_help(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapper

    def on_session_ended(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapper

    def on_stop(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapper

    def on_cancel(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapper

    def on_launch(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # print(self.script['launch'])
            res = f(*args, **kwargs)
            if res:
                return res
            else:
                return self.success(message=self.script['launch'])

        return wrapper

    def success(self, message, message_reprompt=None, card_title=None, card_content=None, small_img=None, large_img=None):
        card = None
        if small_img or large_img:
            card = self._standard_card(title=card_title, content=card_content, small_img=small_img, large_img=large_img)
        elif card_content:
            card = self._simple_card(title=card_title, content=card_content)

        speechlet = self._speechlet(message=message, message_reprompt=message_reprompt, card=card)

        return self._response(speechlet=speechlet)

    def decrypt(self, key):
        return kms.decrypt(
            CiphertextBlob=b64decode(key))['Plaintext'].decode('utf-8')

    def card(self, title, content, small_img=None, large_img=None):
        if small_img or large_img:
            card = self._standard_card(
                title=title,
                content=content,
                small_img=small_img,
                large_img=large_img
            )
        else:
            card = self._simple_card(title=title, content=content)

        return card

    def _validate(self):
        if not os.environ.get('ASK_VERIFY'):
            return True

        if self._validate_app_id() and self._validate_timestamp():
            return True

        return False

    def _track_dynamodb(self, table, **kwargs):
        try:
            item = {
                'request_id': self.request_id,
                'date': self.timestamp,
                'user_id': self.user_id,
                'event': self.event,
                # 'card': kwargs.get('card', {})
            }

            return table.put_item(Item=item)
        except Exception as e:
            logger.error(e)

    def _track_slack(self, webhook, message):
        payload = {'text': message}
        err_msg = 'Problem tracking to Slack'

        try:
            res = requests.post(url=webhook, data=json.dumps(payload))
            if not res.ok:
                logger.error(err_msg, res.text)
        except Exception as e:
            logger.error(err_msg, e)

    def _validate_app_id(self):
        return self.request_app_id == self.app_id

    def _validate_timestamp(self):
        try:
            ts = aniso8601.parse_datetime(self.timestamp())
            dt = datetime.utcnow() - ts.replace(tzinfo=None)

            if abs(dt.total_seconds()) > 150:
                return False
        except Exception as e:
            logger.error('Problem validating request timestamp', e)

            return False

        return True

    def _simple_card(self, title, content):
        return {'type': 'Simple', 'title': title, 'content': content}

    def _standard_card(self, title, content, small_img=None, large_img=None):
        payload = {'type': 'Standard', 'title': title, 'text': content}

        if small_img or large_img:
            # recommend: small 720w x 480h, large 1200w x 800h
            payload['image'] = {}
            if small_img:
                payload['image']['smallImageUrl'] = small_img
            if large_img:
                payload['image']['largeImageUrl'] = large_img

        return payload

    def _link_card(self):
        return {'type': 'LinkAccount'}

    def _speechlet(self, message, message_reprompt=None, card=None):
        payload = {
            'outputSpeech': {
                'type': 'PlainText',
                'text': message
            },
            'shouldEndSession': True
        }

        if card:
            payload['card'] = card

        if message_reprompt:
            payload['reprompt'] = {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': message_reprompt
                }
            }

            payload['shouldEndSession'] = False

        return payload

    def _response(self, speechlet, session_attributes={}):
        return {
            'version': '1.0',
            'sessionAttributes': session_attributes,
            'response': speechlet
        }


class VerificationError(Exception):
    pass
