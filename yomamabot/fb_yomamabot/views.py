from django.shortcuts import render
import json, requests, random, re
from pprint import pprint
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http.response import HttpResponse
from arabicstemmer import ArabicStemmer
stemmer = ArabicStemmer()
from nltk.tokenize import RegexpTokenizer



jokes = {
         's': [""""مرحبا","هل يوجد احد هنا", "هلو",""",
                    """انها ليست سيئة """],
         'Tell ':  ["""The Palestinian Ministry of Communications and Information Technology is the ministry responsible for regulating, managing and monitoring the telecommunications sector in Palestine, and evaluating the performance of the licensed entities, including controlling the prices of their services and the levels of quality of service that must be provided. """,
                    """ The Palestinian Ministry of Communications and Information Technology is the ministry responsible for regulating, managing and monitoring the telecommunications sector in Palestine, and evaluating the performance of the licensed entities, including controlling the prices of their services and the levels of quality of service that must be provided. """],
         'ministry':   ["""The Palestinian Ministry of Communications and Information Technology is the ministry responsible for regulating, managing and monitoring the telecommunications sector in Palestine, and evaluating the performance of the licensed entities, including controlling the prices of their services and the levels of quality of service that must be provided. """,
                    """ The Palestinian Ministry of Communications and Information Technology is the ministry responsible for regulating, managing and monitoring the telecommunications sector in Palestine, and evaluating the performance of the licensed entities, including controlling the prices of their services and the levels of quality of service that must be provided. """],
         }

def post_facebook_message(fbid, recevied_message):
    # Remove all punctuations, lower case the text and split it based on space
    tokens = re.sub(r"[^a-zA-Z0-9\s]",' ',recevied_message).lower().split()
    joke_text = ''
    for token in tokens:
        if token in jokes:
            joke_text = random.choice(jokes[token])
            break
    if not joke_text:
        joke_text = "لا أفهم شيئا"    
    post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token=EAALmU52ZBoyQBOyMXPoF0TESpPMW1JgEF1DT2ZCZBc24JhSKnRdaz6jhrIuw9rwtgc6qZCeZAZALFZClgIbamfM2lk5m2tE0VPp2CpkNs3WVMHx6pY3tOLA8LFL7B8RldZCBW7MZAIg8WdDRNBPQgpGXzgUOOWovTrNvy3hobLSO4rZCzZAyJw4celePufZAmP87Ccp2' 
    response_msg = json.dumps({"recipient":{"id":fbid}, "message":{"text":joke_text}})
    status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
    pprint(status.json())           
    post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token=<page-access-token>' 
    response_msg = json.dumps({"recipient":{"id":fbid}, "message":{"text":recevied_message}})
    status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
    pprint(status.json())
class YoMamaBotView(generic.View):
    def get(self, request, *args, **kwargs):
        if self.request.GET['hub.verify_token'] == '123456':
            return HttpResponse(self.request.GET['hub.challenge'])
        else:
            return HttpResponse('Error, invalid token')
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)    # Post function to handle Facebook messages
    def post(self, request, *args, **kwargs):
        # Converts the text payload into a python dictionary
        incoming_message = json.loads(self.request.body.decode('utf-8'))
        # Facebook recommends going through every entry since they might send
        # multiple messages in a single call during high load
        for entry in incoming_message['entry']:
            for message in entry['messaging']:
                # Check to make sure the received call is a message call
                # This might be delivery, optin, postback for other events 
                if 'message' in message:
                    # Print the message to the terminal
                    pprint(message)
                    # Assuming the sender only sends text. Non-text messages like stickers, audio, pictures
                    # are sent as attachments and must be handled accordingly. 
                    post_facebook_message(message['sender']['id'], message['message']['text'])   
        return HttpResponse()