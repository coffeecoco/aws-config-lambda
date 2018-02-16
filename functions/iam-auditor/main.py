#!/usr/bin/env python
from datetime import datetime, timedelta
import boto3

deactivated = {
    "inactivity": [],
    "age": []
}
sre = []

def deactivate_key(username, key, key_last_used, reason):
    global deactivated, sre
    # don't mess with SRE, we still want to remind them to rotate the key though
    if username in sre:
        print("Skipping deactivating key %s because user %s is in the SRE group." % (key, username))
        return

    if 'LastUsedDate' in key_last_used:
        last_used = key_last_used['LastUsedDate'].replace(tzinfo=None)
    else:
        last_used = "never"

    deactivated[reason].append(
        "{}: {} (Last Used {}, created {})".format(username, key['AccessKeyId'], last_used, key['CreateDate'])
    )
    print("Deactivating %s due to %s." % (deactivated[reason][-1], reason))
    iam = boto3.client('iam')
    resp = iam.update_access_key(
        UserName=username,
        AccessKeyId=key['AccessKeyId'],
        Status='Inactive'
    )
    print(resp)

def notify(message):
    sns = boto3.client('sns')
    resp = sns.publish(
        TopicArn='arn:aws:sns:us-east-1:928401392503:SecurityEvents',
        Message=message,
        Subject='IAM Audit Results'
    )
    print(resp)

def notify_user(username, subject, text):
    ses = boto3.client('ses')
    response = ses.send_email(
        Source='devops@roosterteeth.com',
        Destination={
            'ToAddresses': [
                "%s@roosterteeth.com" % username,
            ]
        },
        Message={
            'Subject': {
                'Data': subject
            },
            'Body': {
                'Html': {
                    'Data': """
Greetings %s,

%s

<p>- With love, the SRE team.</p>
""" % (username, text)
                }
            }
        }
    )
    print(response)

def get_users(group_name=None):
    iam = boto3.client('iam')
    if group_name:
        resp = iam.get_group(MaxItems=1000, GroupName=group_name)
    else:
        resp = iam.list_users(MaxItems=1000)
    if resp['IsTruncated']:
        notify("There are more users in the %s group but the lambda script did not fetch all of them!" % group_name)
    users = map(lambda x: x['UserName'], resp['Users'])
    return users

def lambda_handler(event, context):
    global deactivated, sre
    iam = boto3.client('iam')

    users = get_users()
    engineers = get_users('People')
    sre = get_users('SiteReliabilityEngineers')

    one_months_ago = datetime.utcnow() - timedelta(days=30)
    two_months_ago = datetime.utcnow() - timedelta(days=60)
    almost_three_months_ago = datetime.utcnow() - timedelta(days=80)
    three_months = timedelta(days=90)  # Note: this variable is used when sending email too!
    three_months_ago = datetime.utcnow() - three_months

    for username in users:
        resp = iam.list_access_keys(UserName=username)
        keys = resp['AccessKeyMetadata']

        for key in keys:
            if key['Status'] != 'Active':
                continue
            create_date = key['CreateDate'].replace(tzinfo=None)

            # get last used date
            resp = iam.get_access_key_last_used(
                AccessKeyId=key['AccessKeyId']
            )
            key_last_used = resp['AccessKeyLastUsed']

            # deactivate the key if it hasn't been used for over two months, or one month after it was created if it has never been used at all
            if 'LastUsedDate' in key_last_used:
                last_used_date = key_last_used['LastUsedDate'].replace(tzinfo=None)
                if last_used_date < two_months_ago:
                    deactivate_key(username, key, key_last_used, "inactivity")
                    continue
            elif create_date < one_months_ago:
                deactivate_key(username, key, key_last_used, "inactivity")
                continue

            # if the user is an engineer, deactivate the key if it's more than three months old, or notify the user if it's almost three months old
            if username in engineers:
                if create_date < three_months_ago:
                    deactivate_key(username, key, key_last_used, "age")
                    notify_user(username, 'Your AWS key was deactivated', """
<p>Your AWS key (%s) was deactivated. Please contact the SRE team to have it reactivated. Ask in the #site-reliability channel in Slack.</p>
<p><a href="https://www.youtube.com/watch?v=SrDSqODtEFM">Shame, shame, shame.</a></p>
""" % (key['AccessKeyId']))
                elif create_date < almost_three_months_ago:
                    notify_user(username, 'Your AWS key will expire soon', """
<p>Your AWS key (%s) will expire on %s. Please rotate the key before that to avoid being locked out from AWS. You can rotate it by using a tool called <a href='https://github.com/Fullscreen/aws-rotate-key'>aws-rotate-key</a>.</p>

<p>If you are running Mac, you can rotate your key with the following commands:</p>

<pre>
brew tap fullscreen/tap
brew install aws-rotate-key
aws-rotate-key -y
</pre>

<p>or, if you do not have Homebrew installed:</p>

<pre>
curl -L -o aws-rotate-key-1.0.0-darwin_amd64.zip https://github.com/Fullscreen/aws-rotate-key/releases/download/v1.0.0/aws-rotate-key-1.0.0-darwin_amd64.zip
unzip aws-rotate-key-1.0.0-darwin_amd64.zip
./aws-rotate-key -y
</pre>

<p>If you have issues rotating your key, feel free to ask for help in #site-reliability on Slack.</p>
""" % (key['AccessKeyId'], (create_date+three_months).strftime("%F")))

    print(deactivated)
    message = ""
    if len(deactivated["inactivity"]) > 0:
        message += "\n".join([
            "The following users IAM keys were deactivated due to inactivity:",
            "\n".join(deactivated["inactivity"])
        ])
    if len(deactivated["inactivity"]) > 0 and len(deactivated["age"]) > 0:
        message += "\n\n"
    if len(deactivated["age"]) > 0:
        message += "\n".join([
            "The following users IAM keys were deactivated due to age:",
            "\n".join(deactivated["age"])
        ])
    if len(message) > 0:
        notify(message)


# The code below is only for testing, to run it locally, run:
# AWS_PROFILE=admin ./main.py
if __name__ == "__main__":
    lambda_handler(None, None)
