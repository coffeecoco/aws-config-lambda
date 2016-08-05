#!/usr/bin/env python
import boto3, json

APPLICABLE_RESOURCES = ["AWS::EC2::Volume"]

def evaluate_compliance(volume_id, rule_parameters):
    ec2 = boto3.client("ec2")
    resp = ec2.describe_volumes(VolumeIds=[volume_id])
    volume = resp["Volumes"][0]

    if "MinSize" in rule_parameters and volume["Size"] < int(rule_parameters["MinSize"]):
        return {"ComplianceType": "NOT_APPLICABLE"}

    if volume["State"] == "available":
        return {
            "ComplianceType": "NON_COMPLIANT",
            "Annotation": "Volume %s (%d GB) is not attached to an instance." % (volume_id, volume["Size"])
        }

    elif volume["State"] == "in-use":
        instance_id = volume["Attachments"][0]["InstanceId"]
        resp = ec2.describe_instances(InstanceIds=[instance_id])
        instance = resp["Reservations"][0]["Instances"][0]
        if instance["State"]["Name"] == "stopped":
            return {
                "ComplianceType": "NON_COMPLIANT",
                "Annotation": "Volume %s (%d GB) is in-use but the associated instance (%s) is stopped." % (volume_id, volume["Size"], instance_id)
            }

    return {"ComplianceType": "COMPLIANT"}

def lambda_handler(event, context):
    invoking_event = json.loads(event["invokingEvent"])
    configuration_item = invoking_event["configurationItem"]
    rule_parameters = json.loads(event["ruleParameters"])
    print("Evaluating", configuration_item)
    print("Rule parameters", rule_parameters)

    evaluation = {
        "ComplianceResourceType": configuration_item["resourceType"],
        "ComplianceResourceId": configuration_item["resourceId"],
        "ComplianceType": "NOT_APPLICABLE",
        "OrderingTimestamp": configuration_item["configurationItemCaptureTime"]
    }
    if configuration_item["configurationItemStatus"] != "ResourceDeleted" and configuration_item["resourceType"] in APPLICABLE_RESOURCES:
        evaluation.update(evaluate_compliance(configuration_item["resourceId"], rule_parameters))
    print("Result", evaluation)

    config = boto3.client("config")
    config.put_evaluations(
        Evaluations=[evaluation],
        ResultToken=event["resultToken"]
    )



# The code below is only for testing, to run it locally, simply run ./main.py

if __name__ == "__main__":
    rule_parameters = {"MinSize": "15"}
    for volume_id in ["vol-2e3aeec0", "vol-ab6e40bd", "vol-25abb16e"]:
        print(volume_id, evaluate_compliance(volume_id, rule_parameters))
