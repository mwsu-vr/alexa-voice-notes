"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
import boto3


# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to Alexa voice notes. " \
                    "Would you like to save a message, read your messages, or help?"
                    
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = ""
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying the Alexa Skills Kit sample. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))
    
def get_color_from_session(intent, session):
    session_attributes = {}
    reprompt_text = None

    if session.get('attributes', {}) and "favoriteColor" in session.get('attributes', {}):
        favorite_color = session['attributes']['favoriteColor']
        speech_output = "Your favorite color is " + favorite_color + \
                        ". Goodbye."
        should_end_session = True
    else:
        speech_output = "I'm not sure what your favorite color is. " \
                        "You can say, my favorite color is red."
        should_end_session = False

    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()

def record_new_message(intent, session):
    card_title = intent['name']
    message = intent["slots"]['message']['value']
    receiver = session['attributes']['receiver']
    session_attributes = {"message": message, 'receiver': receiver}
    should_end_session = False
    
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("Messages")
    response = table.get_item(
        Key={'User': receiver}
    )
    msgs = response['Item']['messages']
    msgs.append(message)
    
    table.update_item(
        Key={"User": receiver},
        UpdateExpression="set messages = :r",
        ExpressionAttributeValues={
            ':r': msgs
        }
    )
    
    speech_output = "Message saved for " + receiver + ". What else can I do for you?"
    reprompt_text = "What is your message?"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        
def process_save_intent(intent, session):
    card_title = intent['name']
    receiver = intent['slots']['name']['value']
    session_attributes = {'receiver': receiver}
    should_end_session = False
    
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("Messages")
    response = table.get_item(
        Key={'User': receiver}
    )
    
    if not 'Item' in response.keys():
        speech_output = "No such user exists, dumbass!"
    else:
        speech_output = "What's your message?"
        
    reprompt_text = "Would you like to save a message or read your messages?"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def process_help_intent(intent, session):
    card_title = "Help"
    session_attributes = {}
    should_end_session = False
    
    speech_output = "1. To read messages, say: read messages for name. " \
                    "2. To save a message, say: save message for name. " \
                    "3. To add new user, say: add user name. " \
                    "4. To remove messages, say: delete messages for name. "\
                    "5. When recording a message, begin with: will you, can you, hey, or message is, followed by your message. " \
                    "What else can I do for you? "
        
    reprompt_text = "Would you like to save a message, read your messages, or help?"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        
def read_message(intent, session):
    card_title = intent['name']
    receiver = intent['slots']['name']['value']
    session_attributes = {'receiver': receiver}
    should_end_session = False
    
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("Messages")
    response = table.get_item(
        Key={'User': receiver}
    )
    
    
    speech_output = ''
    if not 'Item' in response.keys():
        speech_output = 'No such user exists, dumbass!'
    elif not response['Item']['messages']:
        speech_output = 'You have no messages. Sad face. '
    else:
        msgs = response['Item']['messages']
        speech_output = ''
        i=1
        for msg in msgs:
            speech_output += 'Message ' + str(i) + ". " + msg + ". "
            i += 1
    
    speech_output += "What else can I do for you?"
    reprompt_text = "What's the name of the receiver?"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def add_user(intent, session):
    name = intent['slots']['name']['value']
    
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("Messages")
    table.put_item(
        Item={
            "User": name,
            "messages": []
        }
    )
    
    speech_output = "New User " + name + " added"
    reprompt_text = "What's the name of the receiver?"
    return build_response({}, build_speechlet_response(
        "CT", speech_output, reprompt_text, False))

def remove_messages(intent, session):
    name = intent['slots']['name']['value']
    
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("Messages")
    table.update_item(
        Key={"User": name},
        UpdateExpression="set messages = :r",
        ExpressionAttributeValues={
            ':r': []
        }
    )
    
    speech_output = "Messages deleted for " + name + ". What else can I do for you?"
    reprompt_text = "What's the name of the receiver?"
    return build_response({}, build_speechlet_response(
        "CT", speech_output, reprompt_text, False))

    
def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "NewMessageIntent":
        return record_new_message(intent, session)
    elif intent_name == "SaveIntent":
        return process_save_intent(intent, session)
    elif intent_name == "ReadMessageIntent":
        return read_message(intent, session)
    elif intent_name == "AddUserIntent":
        return add_user(intent, session)
    elif intent_name == "RemoveMessageIntent":
        return remove_messages(intent, session)
    
    
    elif intent_name == "AMAZON.HelpIntent":
        return process_help_intent(intent, session)
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")

def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
