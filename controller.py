__author__ = "Alon Shrestha"
from config import resourceConfig
from core import startStopInstances, patchExecution, patchExecutionStatusReport, miniPatchComplianceReport


def mainHandler(event, context):
    # Collect parameters
    receivedAction = event["stringParameters"]["action"]
    environment = event["stringParameters"]["environment"]
    receivedAccounts = event["stringParameters"]["account"]

    accountList = []
    for getAccount in resourceConfig.resources:
        accountList.append(getAccount)

    # Check if provided accounts exist in config.
    for account in receivedAccounts:
        if account not in accountList:
            raise ValueError(f"Account: {account} not found in config")

    print(f"Account: {receivedAccounts} found on config. Moving for Action: {receivedAction}")

    # Call Action Method
    if receivedAction == "StartInst":  # Start stopped instance before patching.
        startStopInstances.runStartStop(receivedAction, receivedAccounts, environment)
    elif receivedAction == "RunPatch":  # Run patch.
        patchExecution.runPatchManager(receivedAccounts, environment)
    elif receivedAction == "GenerateReport":  # Generate after patch report.
        patchExecutionStatusReport.generateCommandStatus(environment)
        miniPatchComplianceReport.generateMiniPatchComplianceReport(receivedAccounts, environment)
    elif receivedAction == "StopInst":  # Stop started instance before patching.
        startStopInstances.runStartStop(receivedAction, receivedAccounts, environment)


mainHandler(
    {
        "stringParameters": {
            "action": "StartInst",
            "environment": "DEV",
            "account": ["AccountA"]
        }
    },
    ""
)
