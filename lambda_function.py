# -*- coding: utf-8 -*-
import boto3
import os
import sys
import re
sys.path.append(os.path.join(os.path.dirname(__file__), 'linebotAPI'))

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

def stop_instances(instanceids=[]):
    response = client.stop_instances(InstanceIds=instanceids)
    instances = response.get('StoppingInstances')
    for instance in instances:
        if instance['CurrentState']['Code'] == 64:
            disptext = '停止成功 現在の状態: ' + instance['CurrentState']['Name'] + ' 直前の状態: ' + instance['PreviousState']['Name']
        else:
            disptext = '停止失敗 現在の状態: ' + instance['CurrentState']['Name'] + ' 直前の状態: ' + instance['PreviousState']['Name']
    return disptext


def start_instances(instanceids=[]):
    response = client.start_instances(InstanceIds=instanceids)
    instances = response.get('StartingInstances')
    for instance in instances:
        if instance['CurrentState']['Code'] == 0:
            disptext = '起動成功 現在の状態: ' + instance['CurrentState']['Name'] + ' 直前の状態: ' + instance['PreviousState']['Name']
        else:
            disptext = '起動失敗 現在の状態: ' + instance['CurrentState']['Name'] + ' 直前の状態: ' + instance['PreviousState']['Name']
    return disptext

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

def update_dynamo(instanceid, set_lineid):
    try:
        response = mtable.update_item(
            ExpressionAttributeNames={
                '#G': 'line_rid',
            },
            ExpressionAttributeValues={
                ':g': set_lineid
            },
            Key={
                'id': instanceid ,
                'managed-item': "minecraft-sv-status"
            },
            UpdateExpression='SET #G = :g',
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

    #@handler.add(JoinEvent)
    #def join(line_event):
    #    if hasattr(line_event.source,"group_id"):
    #        update_dynamo(ec2_instanceid[0], line_event.source.group_id)
    #    if hasattr(line_event.source,"room_id"):
    #        update_dynamo(ec2_instanceid[0], line_event.source.room_id)
        
    @handler.add(MessageEvent, message=TextMessage)
    def message(line_event):
        text = line_event.message.text
        if re.match('^startmcsv$', text):
            disptext = start_instances(ec2_instanceid)
            line_bot_api.reply_message(line_event.reply_token, TextSendMessage(text=disptext))
            #if hasattr(line_event.source,"group_id"):
            #    update_dynamo(ec2_instanceid[0], line_event.source.group_id)
            if hasattr(line_event.source,"room_id"):
                update_dynamo(ec2_instanceid[0], line_event.source.room_id)
        elif re.match('^stopmcsv$', text):
            disptext = stop_instances(ec2_instanceid)
            line_bot_api.reply_message(line_event.reply_token, TextSendMessage(text=disptext))
            #if hasattr(line_event.source,"group_id"):
            #    update_dynamo(ec2_instanceid[0], line_event.source.group_id)
            if hasattr(line_event.source,"room_id"):
                update_dynamo(ec2_instanceid[0], line_event.source.room_id)
        elif re.match('^show$', text):
            disptext = show_instances(ec2_instanceid)
            if 'running' in disptext:
                mc_svc_stat = get_servicestat(ec2_instanceid[0])
                disptext += '\nサービス状態：' + mc_svc_stat['service_stat'] + '\nログイン人数：{}'.format(mc_svc_stat['login_num']) \
                            + '\nログインしてる人：' + ','.join(mc_svc_stat['login_user'])
            line_bot_api.reply_message(line_event.reply_token, TextSendMessage(text=disptext))
            #if hasattr(line_event.source,"group_id"):
            #    print(line_event.source.group_id)
            #    update_dynamo(ec2_instanceid[0], line_event.source.group_id)
            #if hasattr(line_event.source,"room_id"):
            #    print(line_event.source.room_id)
            #    update_dynamo(ec2_instanceid[0], line_event.source.room_id)

        if text == "カエレ":
            line_bot_api.reply_message(line_event.reply_token, TextSendMessage("ううっ・・"))
            if hasattr(line_event.source,"group_id"):
                line_bot_api.leave_group(line_event.source.group_id)
            if hasattr(line_event.source,"room_id"):
                line_bot_api.leave_room(line_event.source.room_id)
         

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
