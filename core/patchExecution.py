import json
from config import resourceConfig
from library.globalComponent import sendEmail, getSession, sendDataToS3, getDataFromS3
from datetime import datetime

reportCommand = "PatchCommandId"  # Inorder to upload/download Patch Command ID file from S3.
tableCommandId = ['<html>'
                  '<head><style>table {font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;border-collapse: collapse; } '
                  'td,th{'
                  'border:1px solid #ddd;'
                  'padding:8px;'
                  'width:1%;'
                  '}'
                  '</style>''</head>',
                  '<h2 align="center"><u>\n\n</u></h2><body>']


def runPatchManager(accountProfile, env):
    rebootOption = "RebootIfNeeded" if resourceConfig.rebootAfterPatch else "NoReboot"
    sendPatchedCommandIdDict = resourceConfig.demoJsonWriter
    noPatchedAccount = []
    try:
        for account in accountProfile:
            patchResourceGroupList, resGrp, ec2res, ec2client, ssmClient = getSession(account)
            # Get ResourcesGroupName From Resources Config
            for patchResourceGroup in patchResourceGroupList[env]:
                patchResourceGroupResponse = resGrp.get_group_query(
                    GroupName=patchResourceGroup,
                )
                # Get Patching Tag From ResourceGroup
                patchGroupQuery = json.loads(patchResourceGroupResponse['GroupQuery']['ResourceQuery']['Query'])
                for tagsInResPatchGroup in patchGroupQuery['TagFilters']:
                    for patchCycleTag in tagsInResPatchGroup['Values']:
                        # Send SSM Patch Command With Tag PatchingCycle
                        ssm = ssmClient.send_command(
                            Targets=[
                                {
                                    'Key': 'tag:PatchingCycle',
                                    'Values': [
                                        patchCycleTag,
                                    ]
                                },
                            ],
                            DocumentName='AWS-RunPatchBaseline',
                            DocumentVersion='1',
                            TimeoutSeconds=600,
                            Comment=patchCycleTag,
                            Parameters={"Operation": ["Install"], "RebootOption": [rebootOption]},
                            MaxConcurrency='50',
                            MaxErrors='25',
                        )
                        # Store all run commandIds in dictionary for Email and Status Report and Tracking Purpose.
                        sendPatchedCommandIdDict[account][env][patchCycleTag] = ssm['Command']['CommandId']
    except Exception as e:
        print(f"Something Went Wrong!!! Patch Execution ->  Error: {str(e)}")
        subject = "Error!! Automated Patch " + env + ": Patch Execution On  " + str(datetime.now().date())
        message = 'Something Went Wrong While Starting Instances!! Please Check Logs. Error: ' + str(e)
        bodyMessage = (''.join(message))
        sendEmail(subject, bodyMessage, resourceConfig.toEmailList)
    print(f"SendS3:{sendPatchedCommandIdDict}")
    # Send dictionary Data to s3
    sendDataToS3(reportCommand, sendPatchedCommandIdDict)
    # Get and Read dictionary Data From S3
    getPatchedCommandIdDict = getDataFromS3(reportCommand)
    for account in getPatchedCommandIdDict:
        if getPatchedCommandIdDict[account][env]:
            # Email Command ID
            tableCommandId.append('<table>'
                                  '<tr>'
                                  '<td style="border:5px solid white;" colspan="2"> </td>'
                                  '</tr>'
                                  '<tr>'
                                  '<th style="background-color:#FFBB33" colspan="2">' + account + " Patch Execution Details" + '</th>'
                                  '</tr>'
                                  '<tr>'
                                  '<td> <strong> PatchingCycle Tag </strong> </td>'
                                  '<td> <strong> Command Id </strong> </td>'
                                  '</tr>'
                                  )
            for patchCycleTag, patchedCommandId in getPatchedCommandIdDict[account][env].items():
                print(patchCycleTag, patchedCommandId)
                tableCommandId.append(
                                      '<tr>'
                                      '<td>' + str(patchCycleTag) + '</td>'
                                      '<td>' + str(patchedCommandId) + '</td>'
                                      '</tr>')
        else:
            noPatchedAccount.append(account)
    tableCommandId.append('</table>')
    tableCommandId.append('<h4> <i>Automated</i> </h4>')
    subject = f"Automated Patch {env}: Execution Initiated On {str(datetime.now().date())}"
    bodyMessage = (''.join(tableCommandId))
    sendEmail(subject, bodyMessage, resourceConfig.toEmailList)