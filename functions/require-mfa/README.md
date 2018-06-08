# require-mfa

This function requires an MFA is configured for any IAM user with a login
profile enabled.

## Setup

1. Copy `function.json.example` and input your own IAM role ARN.
2. Run `apex deploy require-mfa`

## Requirements

### Config Rule

Make sure your config rule is configured to trigger on changes
for user resources only.

### IAM Policy

You'll need an IAM role that has access to the IAM and Config API's.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "config:PutEvaluations"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:GetLoginProfile",
                "iam:ListMFADevices"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```
