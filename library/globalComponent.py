import boto3
import json
from config import resourceConfig
from config.resourceConfig import toEmailList
from botocore.config import Config
from datetime import datetime
import time

sts_client = boto3.client('sts')
s3 = boto3.client('s3')

retryConfig = Config(
    retries=dict(
        max_attempts=resourceConfig.maxRetriesCount
    )
)


def getSession(account):
    patchResourceGroupList = resourceConfig.resources[account]['ResourceGroupTag']
    region = resourceConfig.resources[account]['region']
    iamRoleArn = resourceConfig.resources[account]['AssumeIAMRole']
    sts_response = sts_client.assume_role(
        RoleArn=iamRoleArn,
        RoleSessionName='aws-ec2-patch-automation-boto3',
    )
    ssmClient = boto3.client('ssm', aws_access_key_id=sts_response['Credentials']['AccessKeyId'],
                             aws_secret_access_key=sts_response['Credentials']['SecretAccessKey'],
                             aws_session_token=sts_response['Credentials'][
                                 'SessionToken'],
                             region_name=region,
                             config=retryConfig
                             )
    resGrp = boto3.client('resource-groups', aws_access_key_id=sts_response['Credentials']['AccessKeyId'],
                          aws_secret_access_key=sts_response['Credentials']['SecretAccessKey'],
                          aws_session_token=sts_response['Credentials'][
                              'SessionToken'],
                          region_name=region,
                          config=retryConfig)
    ec2res = boto3.resource('ec2',
                            aws_access_key_id=sts_response['Credentials']['AccessKeyId'],
                            aws_secret_access_key=sts_response['Credentials']['SecretAccessKey'],
                            aws_session_token=sts_response['Credentials'][
                                'SessionToken'],
                            region_name=region,
                            config=retryConfig)
    ec2client = boto3.client('ec2',
                             aws_access_key_id=sts_response['Credentials']['AccessKeyId'],
                             aws_secret_access_key=sts_response['Credentials']['SecretAccessKey'],
                             aws_session_token=sts_response['Credentials'][
                                 'SessionToken'],
                             region_name=region,
                             config=retryConfig)

    return patchResourceGroupList, resGrp, ec2res, ec2client, ssmClient


def sendEmail(subject, message, toList):
    try:
        print(f"Sending Email to  {toList}")
        ses = boto3.client('ses', region_name='us-east-1')
        response = ses.send_email(
            Source=resourceConfig.senderEmail,
            Destination={
                'ToAddresses': toList,
            },
            Message={
                'Subject': {
                    'Data': subject
                },
                'Body': {
                    'Html': {
                        'Data': message
                    }

                }

            }
        )
        print("Email Success!!")
    except Exception as e:
        print(f"Email Failed!!, Error: {e}")


def getTag(ec2res, instId, tag):
    ec2instance = ec2res.Instance(instId)
    try:
        if ec2instance.tags:
            for tags in ec2instance.tags:
                if tags["Key"] == tag:
                    instName = tags["Value"]
                    return instName
                else:
                    instName = "Not Define"
            return instName
        else:
            instName = "Not Define"
        return instName
    except:
        return "Not Define"


def sendDataToS3(reportCommand, getData):
    key = ""
    if reportCommand == "PatchCommandId":
        key = resourceConfig.patchCommandIdJson
    elif reportCommand == "RebootInstances":
        key = resourceConfig.rebootInstancesIdJson
    elif reportCommand == "StartStopInstances":
        key = resourceConfig.startStopInstancesIdJson

    # Write data and upload to s3.
    data = getData
    s3.put_object(Bucket=resourceConfig.s3BucketName, Key=key, Body=json.dumps(data))


def getDataFromS3(reportCommand):
    key = ""
    if reportCommand == "PatchCommandId":
        key = resourceConfig.patchCommandIdJson
    elif reportCommand == "RebootInstances":
        key = resourceConfig.rebootInstancesIdJson
    elif reportCommand == "StartStopInstances":
        key = resourceConfig.startStopInstancesIdJson

    # Read data from s3
    response = s3.get_object(Bucket=resourceConfig.s3BucketName, Key=key)
    content = response['Body'].read().decode('utf-8')
    data = json.loads(content)
    return data


def startEc2Inst(ec2client, instId, env, account):
    # Start the EC2 instance with max retries loops
    for i in range(resourceConfig.maxRetriesCount):
        try:
            response = ec2client.start_instances(InstanceIds=[instId])
            print(f'Starting Instance: {instId}, Account: {account}, Env: {env}')
            return "Success"
        except Exception as e:
            print(f'Failed to start instance: {instId} on account: {account} env: {env}, Error: {str(e)}')
            if i < 9:
                print('Retrying in 2 seconds...')
                time.sleep(2)
            else:
                print('Max retries exceeded, sorry giving up.')
                print(
                    f"Sending Email Alert!!! Cannot Start Instance {instId} on {account}")
                subject = "Error!! Automated Patch " + env + ": Failed to Start Instance On  " + str(
                    datetime.now().date())
                message = 'Something went wrong while starting instance!! RetryDetails: 10time3secDelay,  ResourceDetails: InstanceID->' + instId + " On Account->" + account + ' Please Check Error Logs : ' + str(
                    e)
                bodyMessage = (''.join(message))
                sendEmail(subject, bodyMessage, toEmailList)
                return "Failed"


def stopEc2Inst(ec2client, instId, env, account):
    # Stop the EC2 instance with max retries loops
    for i in range(resourceConfig.maxRetriesCount):
        try:
            response = ec2client.stop_instances(InstanceIds=[instId])
            print(f'Stopping Instance: {instId}, Account: {account}, Env: {env}')
            return "Success"
        except Exception as e:
            print(f'Failed to stop instance: {instId} on account: {account} env: {env}, Error: {str(e)}')
            if i < 9:
                print('Retrying in 2 seconds...')
                time.sleep(2)
            else:
                print('Max retries exceeded, sorry giving up.')
                print(
                    f"Sending Email Alert!!! Cannot Stop Instance {instId} on {account}")
                subject = "Error!! Automated Patch " + env + ": Failed to Start Instance On  " + str(
                    datetime.now().date())
                message = 'Something went wrong while starting instance!! RetryDetails: 10time3secDelay,  ResourceDetails: InstanceID-> ' + instId + " On Account->" + account + ' Please Check Error Logs : ' + str(
                    e)
                bodyMessage = (''.join(message))
                sendEmail(subject, bodyMessage, toEmailList)
                return "Failed"
