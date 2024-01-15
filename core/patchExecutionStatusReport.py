from library.globalComponent import sendEmail, getSession, getDataFromS3
from config.resourceConfig import toEmailList
from datetime import datetime

reportCommand = "PatchCommandId"  # Inorder to upload/download Patch Command ID file from S3.
tableCommandStatus = ['<html>'
                      '<head><style>table {font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;border-collapse: collapse; } '
                      'td,th{'
                      'border:1px solid #ddd;'
                      'padding:8px;'
                      'width:1%;'
                      '}'
                      '</style>''</head>',
                      '<h2 align="center"><u>\n\n</u></h2><body>']


def generateCommandStatus(env):
    # Read CommandID from Stored S3
    getPatchedCommandIdData = getDataFromS3(reportCommand)
    for account in getPatchedCommandIdData:
        for environment in getPatchedCommandIdData[account]:
            # Get only the Command ID equal to env variable
            if environment == env:
                if getPatchedCommandIdData[account][env]:
                    tableCommandStatus.append('<table>'
                                              '<tr>'
                                              '<td style="border:5px solid white;" colspan="6"> </td>'
                                              '</tr>'
                                              '<tr>'
                                              '<th style="background-color:#FFBB33" colspan="6">' + account + " Patch Command Details" + '</th>'
                                              '</tr>'
                                              '<td> <strong>PatchCycleTag</strong> </td>'
                                              '<td> <strong>CommandID</strong> </td>'
                                              '<td> <strong>TargetInTag</strong> </td>'
                                              '<td> <strong>TargetInPatch</strong> </td>'
                                              '<td> <strong>FailedTargetInPatch</strong> </td>'
                                              '<td> <strong>OverallStatus</strong> </td>'
                                              '<tr>'
                                              '</tr>'

                                      )

                    for patchingTag, commandId in getPatchedCommandIdData[account][env].items():
                        patchResourceGroupList, resGrp, ec2res, ec2client, ssmClient = getSession(account)
                        # Get response of commandID from list_commands
                        commandResponse = ssmClient.list_commands(
                            CommandId=commandId,
                        )
                        # Get the count of ec2 instances in Patching Tag
                        ec2CountResponse = ec2client.describe_instances(
                            Filters=[
                                {
                                    'Name': 'tag:PatchingCycle',
                                    'Values': [
                                        patchingTag,
                                    ]
                                },
                            ],
                        )
                        instCounter = 0
                        for reservations in ec2CountResponse['Reservations']:
                            for instance in reservations['Instances']:
                                instCounter += 1
                        for command in commandResponse['Commands']:
                            if command['Status'] == "Success":
                                if instCounter == command['TargetCount']:
                                    if command['ErrorCount'] != 0:
                                        print("1")
                                        print(account, patchingTag,  commandId, instCounter, command['TargetCount'], command['ErrorCount'], "Failed")
                                        # Condition Status=Success, Ec2TagCount=Ec2CommandCount, FailedCount > 0
                                        tableCommandStatus.append(
                                            '<tr>'
                                            '<td>' + patchingTag + '</td>'
                                            '<td>' + commandId + '</td>'
                                            '<td>' + str(instCounter) + '</td>'
                                            '<td>' + str(command['TargetCount']) + '</td>'
                                            '<td style="background-color:#FA5B39">' + str(command['ErrorCount']) + '</td>'  # Red
                                            '<td style="background-color:#FA5B39"> Failed </td>'  # Red
                                            '</tr>'
                                        )
                                    else:
                                        # Condition Status=Success, Ec2TagCount=Ec2CommandCount, FailedCount = 0
                                        print("2")
                                        print(account, patchingTag, commandId, instCounter, command['TargetCount'],
                                              command['ErrorCount'], "Success")
                                        tableCommandStatus.append(
                                            '<tr>'
                                            '<td>' + patchingTag + '</td>'
                                            '<td>' + commandId + '</td>'
                                            '<td>' + str(instCounter) + '</td>'
                                            '<td>' + str(command['TargetCount']) + '</td>'
                                            '<td>' + str(command['ErrorCount']) + '</td>'
                                            '<td style="background-color:#61FF33"> Success </td>'  # Green
                                            '</tr>'
                                        )
                                else:
                                    print("3")
                                    # Condition Status=Success, Ec2TagCount!=Ec2CommandCount, FailedCount > 0
                                    if command['ErrorCount'] != 0:
                                        print(account, patchingTag,  commandId, instCounter, command['TargetCount'], command['ErrorCount'], "Failed")
                                        tableCommandStatus.append(
                                            '<tr>'  # red
                                            '<td>' + patchingTag + '</td>'
                                            '<td>' + commandId + '</td>'
                                            '<td style="background-color:#FCFF33">' + str(instCounter) + '</td>'  # Yellow
                                            '<td style="background-color:#FCFF33">' + str(command['TargetCount']) + '</td>' # Yellow
                                            '<td style="background-color:#FA5B39">' + str(command['ErrorCount']) + '</td>'
                                            '<td style="background-color:#FA5B39" > Failed </td>'  # Red
                                            '</tr>'
                                        )
                                    else:
                                        # Condition Status=Success, Ec2TagCount!=Ec2CommandCount, FailedCount = 0
                                        print("4")
                                        print(account, patchingTag, commandId, instCounter, command['TargetCount'],
                                              command['ErrorCount'], "Success")
                                        tableCommandStatus.append(
                                            '<tr>'
                                            '<td>' + patchingTag + '</td>'
                                            '<td>' + commandId + '</td>'
                                            '<td style="background-color:#FCFF33">' + str(instCounter) + '</td>'  # Yellow
                                            '<td style="background-color:#FCFF33">' + str(command['TargetCount']) + '</td>'  # Yellow
                                            '<td>' + str(command['ErrorCount']) + '</td>'
                                            '<td style="background-color:#61FF33"> Success </td>'  # Green
                                            '</tr>'
                                        )
                            else:
                                print("5")
                                if instCounter == command['TargetCount']:
                                    if command['ErrorCount'] != 0:
                                        # Condition Status!=Success, Ec2TagCount=Ec2CommandCount, FailedCount > 0
                                        print(account, patchingTag, commandId, instCounter, command['TargetCount'],
                                              command['ErrorCount'], "InProgress")
                                        tableCommandStatus.append(
                                            '<tr>'
                                            '<td>' + patchingTag + '</td>'
                                            '<td>' + commandId + '</td>'
                                            '<td>' + str(instCounter) + '</td>'
                                            '<td>' + str(command['TargetCount']) + '</td>'
                                            '<td style="background-color:#FA5B39">' + str(command['ErrorCount']) + '</td>' # Red
                                            '<td style="background-color:#FCFF33"> InProgress </td>'  # Yellow
                                            '</tr>'
                                        )
                                    else:
                                        # Condition Status!=Success, Ec2TagCount=Ec2CommandCount, FailedCount = 0
                                        print("6")
                                        print(account, patchingTag, commandId, instCounter, command['TargetCount'],
                                              command['ErrorCount'], "InProgress")
                                        tableCommandStatus.append(
                                            '<tr>'
                                            '<td>' + patchingTag + '</td>'
                                            '<td>' + commandId + '</td>'
                                            '<td>' + str(instCounter) + '</td>'
                                            '<td>' + str(command['TargetCount']) + '</td>'
                                            '<td>' + str(command['ErrorCount']) + '</td>'
                                            '<td style="background-color:#FCFF33"> InProgress </td>'  # Yellow
                                            '</tr>'
                                        )
                                else:
                                    print("7")
                                    if command['ErrorCount'] != 0:
                                        # Condition Status!=Success, Ec2TagCount=Ec2CommandCount, FailedCount > 0
                                        print(account, patchingTag, commandId, instCounter, command['TargetCount'],
                                              command['ErrorCount'], "InProgress")
                                        tableCommandStatus.append(
                                            '<tr>'
                                            '<td>' + patchingTag + '</td>'
                                            '<td>' + commandId + '</td>'
                                            '<td style="background-color:#FCFF33">' + str(instCounter) + '</td>'  # Yellow
                                            '<td style="background-color:#FCFF33">' + str(command['TargetCount']) + '</td>'  # Yellow
                                            '<td style="background-color:#FA5B39">' + str(command['ErrorCount']) + '</td>'
                                            '<td style="background-color:#FA5B39"> InProgress </td>'  # Yellow
                                            '</tr>'
                                        )
                                    else:
                                        print("8")
                                        # Condition Status!=Success, Ec2TagCount=Ec2CommandCount, FailedCount = 0
                                        print(account, patchingTag, commandId, instCounter, command['TargetCount'],
                                              command['ErrorCount'], "InProgress")
                                        tableCommandStatus.append(
                                            '<tr>'  # yellow
                                            '<td>' + patchingTag + '</td>'
                                            '<td>' + commandId + '</td>'
                                            '<td style="background-color:#FCFF33">' + str(instCounter) + '</td>'  # Yellow
                                            '<td style="background-color:#FCFF33">' + str(command['TargetCount']) + '</td>'  # Yellow
                                            '<td>' + str(command['ErrorCount']) + '</td>'
                                            '<td style="background-color:#FCFF33"> InProgress </td>'  # Yellow
                                            '</tr>'
                                        )

    tableCommandStatus.append('</table>')
    tableCommandStatus.append('<h4> <i>Automated</i> </h4>')
    subject = f"Automated Patch {env}: Completion Report On {str(datetime.now().date())}"
    bodyMessage = (''.join(tableCommandStatus))
    sendEmail(subject, bodyMessage, toEmailList)
