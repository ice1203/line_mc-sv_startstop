#!/bin/bash
#awsconfig_dir=/root/.aws
DATE=`date +%y%m%d%H%M`
if [ $# -lt 2 ];then
 echo "ex:$0 <dl|ul> function-name profile-name"
 echo "profile-name list."
 grep '\[' ${awsconfig_dir}/config
 exit
fi
FILEN=temp_lambdacode_${2}_${DATE}.zip
if [ -f $FILEN ];then
 echo "exists $FILEN"
 exit
fi

if [ "$1" = "dl" ];then
 URLtxt=`aws lambda get-function --function-name $2 --region ap-northeast-1  --query 'Code.Location' --output text`
 curl -o $FILEN $URLtxt
 unzip $FILEN
 rm $FILEN
elif [ "$1" = "ul" ];then
 zip -r /tmp/${FILEN} *
 aws lambda \
    update-function-code \
    --region ap-northeast-1
    --function-name $2 \
    --zip-file fileb:///tmp/${FILEN} \
    --publish
 rm /tmp/${FILEN}
fi
