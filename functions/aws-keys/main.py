#!/usr/bin/env python
from datetime import datetime, timedelta, tzinfo
import boto3, json

APPLICABLE_RESOURCES = ["AWS::IAM::User"]

def evaluate_compliance(user_name, rule_parameters):
    iam = boto3.client("iam")
    access_keys = iam.list_access_keys(UserName=user_name)
    active_keys = filter(lambda key: key["Status"] == "Active", access_keys["AccessKeyMetadata"])

    if len(active_keys) == 0:
        return {"ComplianceType": "NOT_APPLICABLE"}
    elif len(active_keys) > 1:
        return {
            "ComplianceType": "NON_COMPLIANT",
            "Annotation": "User has two active keys."
        }

    some_time_ago = datetime.utcnow() - timedelta(days=int(rule_parameters["NumDays"]))
    key = active_keys[0]
    create_date = key["CreateDate"].replace(tzinfo=None)
    delta = datetime.utcnow() - create_date

    return {
        "ComplianceType": "NON_COMPLIANT" if create_date < some_time_ago else "COMPLIANT",
        "Annotation": "Key is %d days old." % (delta.days)
    }

def lambda_handler(event, context):
    invoking_event = json.loads(event["invokingEvent"])
    configuration_item = invoking_event["configurationItem"]
    rule_parameters = json.loads(event["ruleParameters"])
    if "NumDays" not in rule_parameters:
        rule_parameters["NumDays"] = "90"

    print("Evaluating", configuration_item)
    print("Rule parameters", rule_parameters)

    evaluation = {
        "ComplianceResourceType": configuration_item["resourceType"],
        "ComplianceResourceId": configuration_item["resourceId"],
        "ComplianceType": "NOT_APPLICABLE",
        "OrderingTimestamp": configuration_item["configurationItemCaptureTime"]
    }
    if configuration_item["configurationItemStatus"] != "ResourceDeleted" and configuration_item["resourceType"] in APPLICABLE_RESOURCES:
        evaluation.update(evaluate_compliance(configuration_item["resourceName"], rule_parameters))
    print("Result", evaluation)

    config = boto3.client("config")
    config.put_evaluations(
        Evaluations=[evaluation],
        ResultToken=event["resultToken"] if "resultToken" in event else "No token found."
    )



# The code below is only for testing, to run it locally, simply run ./main.py

if __name__ == "__main__":
    rule_parameters = {"NumDays": "30"}
    for user_name in ["john.doe"]:
        print(user_name, evaluate_compliance(user_name, rule_parameters))
