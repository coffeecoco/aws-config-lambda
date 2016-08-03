# aws-config-lambda

A collection of lambda functions that can be use to enforce various types
of compliance with AWS Config rules.

# Apex

This repository assumes the use of [Apex](http://apex.run) for deploying
lambda functions in AWS.

# Installation

## 1. Configure IAM roles

You will need to configure IAM roles for the functions you want to deploy. There
is a policy.json file defined for each function that describes the IAM policy
permissions required for the function to run.

## 2. Create function.json

Before deploying a function, copy the function.json.example file to function.json
and update the value of the `role` key to the ARN of the role(s) you created
in step 1.

## 3. Deploy the function

Deploy the function(s) with `apex deploy`

## 4. Create Config rule

Create a new rule in AWS Config using the lambda function you just deployed.
https://docs.aws.amazon.com/config/latest/developerguide/evaluate-config_develop-rules_getting-started.html
