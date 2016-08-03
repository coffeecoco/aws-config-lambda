#!/usr/bin/env python

import boto3, json

iam = boto3.client('iam')
config = boto3.client('config')

APPLICABLE_RESOURCES = ["AWS::IAM::User"]

def has_login_profile(user):
  try:
    iam.get_login_profile(UserName=user['UserName'])
    return True
  except:
    return False

def has_mfa_configured(user):
  resp = iam.list_mfa_devices(UserName=user['UserName'])
  if len(resp['MFADevices']) == 0:
    return False
  else:
    return True

def evaluate_compliance(configuration_item):
  if configuration_item["resourceType"] not in APPLICABLE_RESOURCES:
    return "NOT_APPLICABLE"

  resource_information = config.get_resource_config_history(
    resourceType=configuration_item["resourceType"],
    resourceId=configuration_item["resourceId"]
  )
  user_name = resource_information["configurationItems"][0]["resourceName"]
  print('User name: {}'.format(user_name))

  user = {'UserName': user_name}
  if has_login_profile(user) == False:
    return "NOT_APPLICABLE"

  if has_mfa_configured(user):
    return "COMPLIANT"

  return "NON_COMPLIANT"

def lambda_handler(event, context):
  invoking_event = json.loads(event["invokingEvent"])
  configuration_item = invoking_event["configurationItem"]
  print("Evaluating item")
  print(configuration_item)
  result_token = "No token found."
  if "resultToken" in event:
      result_token = event["resultToken"]

  evals = [{ "ComplianceResourceType":
               configuration_item["resourceType"],
             "ComplianceResourceId":
               configuration_item["resourceId"],
             "ComplianceType":
               evaluate_compliance(configuration_item),
             "OrderingTimestamp":
               configuration_item["configurationItemCaptureTime"]
          }]
  print(evals)
  config.put_evaluations(
    Evaluations=evals,
    ResultToken=result_token
  )
