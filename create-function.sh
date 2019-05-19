#!/bin/bash
FunctionName=$1
RoleName=$2
AccountID=`aws sts get-caller-identity --profile ${Profile} | jq -r '.Account'`
DATE=`date +%y%m%d%H%M`
FILEN=temp_lambdacode_${2}_${DATE}.zip

zip -r /tmp/${FILEN} *
aws lambda create-function \
    --function-name ${FunctionName} \
    --zip-file fileb:///tmp/${FILEN} \
    --handler lambda_function.lambda_handler \
    --runtime python3.6 \
    --role  \
    --layers  ${Layer} \
    --timeout 90 \
    --environment Variables="{EC2_INSTANCEID=test,LINE_CHANNEL_SECRET=test,LINE_CHANNEL_ACCESS_TOKEN=test}" \
    --region ap-northeast-1

rm -f /tmp/${FILEN}
