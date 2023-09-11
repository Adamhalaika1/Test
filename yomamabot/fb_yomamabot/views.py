from django.shortcuts import render
import json
import requests
import random
import re
import numpy as np
import tensorflow as tf
import tflearn
import pickle
from pprint import pprint
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http.response import HttpResponse
from arabicstemmer import ArabicStemmer
from nltk.tokenize import RegexpTokenizer

# Load pickle data
data = pickle.load(open("training_data", "rb"))
words = data['words']
classes = data['classes']

train_x = data['train_x']
train_y = data['train_y']

# Initialize and load the model
net = tflearn.input_data(shape=[None, len(train_x[0])])
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, len(train_y[0]), activation='softmax')
net = tflearn.regression(net)
model = tflearn.DNN(net)
model.load('./model.tflearn')

stemmer = ArabicStemmer()
tokenizer = RegexpTokenizer(r'\w+')


print("Processing the Intents.....")
with open('intents.json') as json_data:
    intents = json.load(json_data)

arabic_stop_words = set([
    "أ", "إ", "في", "من", "على", "عن", "مع", "إلى",
    "هذا", "هذه", "هؤلاء", "ذلك", "ذلكم", "هما",
    "هم", "هي", "هو", "ليس", "كان", "لم", "لن",
    "له", "لها", "أن", "عليه", "عليها", "إذا", "عند",
    "كل", "كما", "كأن", "فقط", "فيه", "قد", "قبل",
    "مثل", "منذ", "حتى", "حوالي", "عشر", "عدة",
    "عدد", "كانت", "بين", "بيد", "أيضا", "ضمن",
    "طالما", "عام", "إلخ", "إلا", "ماذا", "منها",
    "يوم", "أول", "آخر", "واحد", "فيها", "أنا", "أنت",
    "نحن", "أنتم", "هم", "هي", "هو", "أنا", "أنت",
    "نحن", "أنتم", "هم", "هي", "هو"
    # Add more words as needed
])

# Helper functions
def clean_up_sentence(sentence):
    sentence_words = tokenizer.tokenize(sentence)
    sentence_words = [stemmer.light_stem(
        w) for w in sentence_words if w not in arabic_stop_words]
    return sentence_words


def bow(sentence, words):
    sentence_words = clean_up_sentence(sentence)
    bag = [0]*len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                bag[i] = 1
    return np.array(bag)


# Main function to handle Facebook messages
def post_facebook_message(fbid, received_message):
    # Preprocess the received message
    sentence_words = clean_up_sentence(received_message)
    bag = bow(sentence_words, words)

    # Predict the category
    results = model.predict([np.array(bag)])[0]
    results_index = np.argmax(results)
    tag = classes[results_index]

    # Generate a response based on the predicted category
    for intent in intents['intents']:
        if intent['tag'] == tag:
            response = random.choice(intent['responses'])
            break
    else:
        response = "I didn't understand that."

    # Send the response back to Facebook Messenger
    post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token=EAALmU52ZBoyQBOyMXPoF0TESpPMW1JgEF1DT2ZCZBc24JhSKnRdaz6jhrIuw9rwtgc6qZCeZAZALFZClgIbamfM2lk5m2tE0VPp2CpkNs3WVMHx6pY3tOLA8LFL7B8RldZCBW7MZAIg8WdDRNBPQgpGXzgUOOWovTrNvy3hobLSO4rZCzZAyJw4celePufZAmP87Ccp2' 
    response_msg = json.dumps(
        {"recipient": {"id": fbid}, "message": {"text": response}})
    requests.post(post_message_url, headers={
                  "Content-Type": "application/json"}, data=response_msg)


class YoMamaBotView(generic.View):
    def get(self, request, *args, **kwargs):
        if self.request.GET['hub.verify_token'] == '123456':
            return HttpResponse(self.request.GET['hub.challenge'])
        else:
            return HttpResponse('Error, invalid token')

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        # Post function to handle Facebook messages
        return generic.View.dispatch(self, request, *args, **kwargs)

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
                    post_facebook_message(
                        message['sender']['id'], message['message']['text'])
        return HttpResponse()
