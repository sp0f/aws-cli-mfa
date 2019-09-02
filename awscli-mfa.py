#!/usr/bin/env python3
import boto3
import botocore
import configparser
import os
import argparse

token_duration=32400
aws_config_path=os.path.expanduser("~/.aws/credentials")
mfa_profile_name="mfa"

# get user data
sts_client = boto3.client('sts')
callerIdentity = sts_client.get_caller_identity()
account_id=callerIdentity['Account']
user_arn=callerIdentity['Arn']
user_mfa_arn=user_arn.replace(":user/",":mfa/") # don't want to use IAM (dirty hack)

# get MFA key

parser = argparse.ArgumentParser()
parser.add_argument("-m",'--mfa', required=False, help="MFA token code")
args=parser.parse_args()

# if command line argument was provided
if args.mfa is None:
    mfa_token=input("Enter the MFA code: ")
else:
    mfa_token=args.mfa

# get temporary credentials
try:
    credentials=sts_client.get_session_token(
        DurationSeconds=token_duration,
        SerialNumber=user_mfa_arn,
        TokenCode=mfa_token
    )
except botocore.exceptions.ClientError as err:
    if err.response["Error"]["Message"] == "Cannot call GetSessionToken with session credentials":
        print("You are already using session token. Exiting")
    else:
        raise err

# parse ~/.aws/config

# update ~/.aws/credentials
config = configparser.ConfigParser()

with open(aws_config_path, 'r+') as configfile:
    config.read(aws_config_path)

    if config.has_section('mfa'):
        config.set(mfa_profile_name,"aws_access_key_id",credentials["Credentials"]["AccessKeyId"])
        config.set(mfa_profile_name,"aws_secret_access_key",credentials["Credentials"]["SecretAccessKey"])
        config.set(mfa_profile_name,"aws_session_token",credentials["Credentials"]["SessionToken"])
        config.write(configfile)
    else:
        config.add_section(mfa_profile_name)
        config.set(mfa_profile_name,"aws_access_key_id",credentials["Credentials"]["AccessKeyId"])
        config.set(mfa_profile_name,"aws_secret_access_key",credentials["Credentials"]["SecretAccessKey"])
        config.set(mfa_profile_name,"aws_session_token",credentials["Credentials"]["SessionToken"])
        config.write(configfile)
