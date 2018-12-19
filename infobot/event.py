import json
import os
import re
import boto3
from boto3.dynamodb.conditions import Key
from slackclient import SlackClient

BOT_TOKEN = os.environ['BOT_TOKEN']
SENTIMENT_TABLE = os.environ['SENTIMENT_TABLE']

sc = SlackClient(BOT_TOKEN)
ddb = boto3.resource('dynamodb')
comprehend = boto3.client('comprehend')
sentiment_table = ddb.Table(SENTIMENT_TABLE)

def receive(event, context):
    data = json.loads(event['body'])
    print("Got data: {}".format(data))
    return_body = "ok"

    if data["type"] == "url_verification":
        print("Received challenge")
        return_body = data["challenge"]
    elif (
        data["type"] == "event_callback" and
        data["event"]["type"] == "message" and
        "subtype" not in data["event"]
    ):
        handle_message(data)

    return {
        "statusCode": 200,
        "body": return_body
    }

def handle_message(data):
    sentiment = get_sentiment(data["event"]["text"])
    reaction = get_reaction(sentiment)
    reaction_response = send_reaction(data["event"]["channel"], reaction, data["event"]["ts"])
    print(reaction_response)
    
def get_sentiment(text):
    sentiment = comprehend.detect_sentiment(
        Text=text,
        LanguageCode='en'
    )
    return(sentiment['Sentiment'])

def get_reaction(sentiment):
    if sentiment == "POSITIVE":
        reaction = "thumbsup"
    elif sentiment == "NEGATIVE":
        reaction = "thumbsdown"
    elif sentiment == "NEUTRAL":
        reaction = "neutral_face"
    elif sentiment == "MIXED":
        reaction = "shrug"
    return(reaction)

def send_reaction(channel, reaction, timestamp):
    response = sc.api_call(
        "reactions.add",
        channel=channel,
        name=reaction,
        timestamp=timestamp
    )
    return(response['ok'])