# -*- coding: utf-8 -*-
import boto3
import os
import sys
import re
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, JoinEvent, TextMessage, TextSendMessage,
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
import logging
from botocore.exceptions import ClientError

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
dynamodb = boto3.resource('dynamodb')
mtable    = dynamodb.Table('managed-table')

def show_instances(instanceids=[]):
    response = client.describe_instance_status(InstanceIds=instanceids,IncludeAllInstances=True)
    instances = response.get('InstanceStatuses')
    for instance in instances:
        disptext = '現在の状態: ' + instance['InstanceState']['Name']
    return disptext

def get_servicestat(instanceid):
    try:
        response = mtable.get_item(
            Key={
                'id': instanceid ,
                'managed-item': "minecraft-sv-status"
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        #item = response['Item']
        print("dynamodb GetItem succeeded:")
        #print(json.dumps(item, indent=4, cls=DecimalEncoder))
        return response['Item']

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

    try:
        line_bot_api.push_message('C52e1a5a0fc25d52407cbe412a2f37967', TextSendMessage(text='Hello World!'))
    except LineBotApiError as e:
        logger.error("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            logger.error("  %s: %s" % (m.property, m.message))
        return error_json
    except InvalidSignatureError:
        return error_json

    return ok_json
