# -*- coding: utf-8 -*-
import boto3
import os
import sys
import re
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2_instanceid = [ os.getenv('EC2_INSTANCEID', None) ]

channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    logger.error('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    logger.error('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)
client = boto3.client('ec2')

def stop_instances(instances=[]):
    response = client.stop_instances(InstanceIds=instances)
    instances = response.get('StoppingInstances')
    for instance in instances:
        if instance['CurrentState']['Code'] == 64:
            disptext = '停止成功 現在の状態: ' + instance['CurrentState']['Name'] + ' 直前の状態: ' + instance['PreviousState']['Name']
        else:
            disptext = '停止失敗 現在の状態: ' + instance['CurrentState']['Name'] + ' 直前の状態: ' + instance['PreviousState']['Name']
    return disptext


def start_instances(instances=[]):
    response = client.start_instances(InstanceIds=instances)
    instances = response.get('StartingInstances')
    for instance in instances:
        if instance['CurrentState']['Code'] == 0:
            disptext = '起動成功 現在の状態: ' + instance['CurrentState']['Name'] + ' 直前の状態: ' + instance['PreviousState']['Name']
        else:
            disptext = '起動失敗 現在の状態: ' + instance['CurrentState']['Name'] + ' 直前の状態: ' + instance['PreviousState']['Name']
    return disptext

def show_instances(instances=[]):
    response = client.describe_instance_status(InstanceIds=instances,IncludeAllInstances=True)
    instances = response.get('InstanceStatuses')
    for instance in instances:
        disptext = '現在の状態: ' + instance['InstanceState']['Name']
    return disptext

def lambda_handler(event, context):
    signature = event["headers"]["X-Line-Signature"]
    body = event["body"]
    ok_json = {"isBase64Encoded": False,
               "statusCode": 200,
               "headers": {},
               "body": ""}
    error_json = {"isBase64Encoded": False,
                  "statusCode": 403,
                  "headers": {},
                  "body": "Error"}

    @handler.add(MessageEvent, message=TextMessage)
    def message(line_event):
        text = line_event.message.text
        if re.match('^startmcsv$', text):
            disptext = start_instances(ec2_instanceid)
            line_bot_api.reply_message(line_event.reply_token, TextSendMessage(text=disptext))
        elif re.match('^stopmcsv$', text):
            disptext = stop_instances(ec2_instanceid)
            line_bot_api.reply_message(line_event.reply_token, TextSendMessage(text=disptext))
        elif re.match('^show$', text):
            disptext = show_instances(ec2_instanceid)
            line_bot_api.reply_message(line_event.reply_token, TextSendMessage(text=disptext))

    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        logger.error("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            logger.error("  %s: %s" % (m.property, m.message))
        return error_json
    except InvalidSignatureError:
        return error_json

    return ok_json
