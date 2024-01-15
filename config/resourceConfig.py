# Auto Reboot After Patch Option
rebootAfterPatch = True

# Max Retries In Failed Cases
maxRetriesCount = 10  # Used when instance fails to start or get session.

# Email Config
toEmailList = ["receiver@something-example.com"]
senderEmail = "admin@something-example.com"



# S3 Bucket For Storing Patching Progress State
s3BucketName = "your-bucket-name"

# Patching Progress State Files
s3bucketConfigPrefixPath = "PatchAutomationStateFiles/"
patchCommandIdJson = f"{s3bucketConfigPrefixPath}patchedCommandId.json"
rebootInstancesIdJson = f"{s3bucketConfigPrefixPath}rebootInstances.json"
startStopInstancesIdJson = f"{s3bucketConfigPrefixPath}stoppedInstances.json"

# Ec2 Resources Config
resources = {
    "AccountA":
        {
            "id": "123XXXXXX89",
            "region": "us-east-1",
            "ResourceGroupTag": {
                "DEV": ['PatchCycle-Dev'],
                "QC": ['PatchCycle-QC'],
                "UAT": ['PatchCycle-UAT'],
                "PROD": ['PatchCycle-PROD']
            },
            "AssumeIAMRole": "arn:aws:iam::123XXXXXX89:role/access_cross_account_example"

        },
    "AccountB":
        {
            "id": "1234123XX34XX8",
            "region": "us-east-2",
            "ResourceGroupTag": {
                "DEV": ['PatchCycle-Dev'],
                "PROD": ['PatchCycle-PROD']
            },
            "AssumeIAMRole": "arn:aws:iam::1234123XX34XX8:role/access_cross_account_example"
        }
}

# State Store Json Config
demoJsonWriter = {
    "AccountA": {"DEV": {}, "QC": {}, "UAT": {}, "Prod": {}},
    "AccountB": {"DEV": {}, "QC": {}, "UAT": {}, "Prod": {}}
    }


