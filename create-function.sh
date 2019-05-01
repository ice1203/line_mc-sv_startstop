#!/bin/bash
if [ $# -ne 3 ]; then
  echo "指定された引数は$#個です。" 1>&2
  echo "実行するには3個の引数が必要です。" 1>&2
  echo "$0 [LambdaFunctionName] [Role] [AWS CLI Profile]"
  exit 1
fi
FunctionName=$1
RoleName=$2
Profile=$3
AccountID=`aws sts get-caller-identity --profile ${Profile} | jq -r '.Account'`
DATE=`date +%y%m%d%H%M`
FILEN=temp_lambdacode_${2}_${DATE}.zip

zip -r /tmp/${FILEN} *
aws lambda create-function \
    --function-name ${FunctionName} \
    --zip-file fileb:///tmp/${FILEN} \
    --handler lambda_function.lambda_handler \
    --runtime python3.6 \
    --role arn:aws:iam::${AccountID}:role/${RoleName} \
    --layers  ${Layer} \
    --timeout 90 \
    --environment Variables="{EC2_INSTANCEID=test,LINE_CHANNEL_SECRET=test,LINE_CHANNEL_ACCESS_TOKEN=test}" \
    --region ap-northeast-1 \
    --profile ${Profile}

rm -f /tmp/${FILEN}
