import json
from config import resourceConfig
from library.globalComponent import getTag, getSession, sendEmail, \
    getDataFromS3, sendDataToS3, startEc2Inst, stopEc2Inst
import time
from datetime import datetime


reportCommand = "StartStopInstances"  # Inorder to upload/download Start/Stop Instance ID file from S3.
tableSratStopInst = ['<html>'
                 '<head><style>table {font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;border-collapse: collapse; } '
                 'td,th{'
                 'border:1px solid #ddd;'
                 'padding:8px;'
                 'width:1%;'
                 '}'
                 '</style>''</head>',
                 '<h2 align="center"><u>\n\n</u></h2><body>']


def runStartStop(action, accountProfile, env):
    sendStartStopInstancesDict = resourceConfig.demoJsonWriter
    if action == "StartInst":
        # Start Instances Before Patching
        for account in accountProfile:
            try:
                patchGroupList, resGrp, ec2res, ec2client, ssmClient = getSession(account)
                for patchGroup in patchGroupList[env]:
                    patchGroupResponse = resGrp.get_group_query(
                        GroupName=patchGroup,
                    )
                    patchGroupQuery = json.loads(patchGroupResponse['GroupQuery']['ResourceQuery']['Query'])
                    for tagsInResPatchGroup in patchGroupQuery['TagFilters']:
                        for patchCycleTag in tagsInResPatchGroup['Values']:
                            print("Checking Stopped Instances ->", account, "->", patchCycleTag)
                            ec2 = ec2client.describe_instances(
                                Filters=[
                                    {
                                        'Name': 'tag:PatchingCycle',
                                        'Values': [patchCycleTag]
                                    },
                                    {
                                        'Name': 'instance-state-name',
                                        'Values': ['stopped']
                                    }
                                ],
                            )
                            if ec2['Reservations']:
                                for reservation in ec2['Reservations']:
                                    for inst in reservation['Instances']:
                                        # Starting Instances before patch.
                                        response = startEc2Inst(ec2client, inst['InstanceId'], env, account)
                                        if response == "Success":
                                            # Collect Data in Dictionary
                                            if patchCycleTag not in sendStartStopInstancesDict[account][env]:
                                                sendStartStopInstancesDict[account][env][patchCycleTag] = {}
                                            sendStartStopInstancesDict[account][env][patchCycleTag][
                                                inst['InstanceId']] = getTag(ec2res, inst['InstanceId'],
                                                                             "Name")
            except Exception as e:
                print(f"Something went wrong!!! Cannot Start Resource on {account}, Error: {str(e)}")
                subject = "Error!! Automated Patch " + env + ": Failed to Start Instance On  " + str(datetime.now().date())
                message = 'Something Went Wrong While Starting Instances!! Account: ' + account + '. Please Check Error Logs: ' + str(e)
                bodyMessage = (''.join(message))
                sendEmail(subject, bodyMessage, resourceConfig.toEmailList)

        print(f"SendData: {sendStartStopInstancesDict}")
        # Send Data to S3
        sendDataToS3(reportCommand, sendStartStopInstancesDict)

        # Buffer time for upload.
        time.sleep(5)
        # Get Data from S3
        getStoppedInst = getDataFromS3(reportCommand)
        for account in getStoppedInst:
            for environment in getStoppedInst[account]:
                if environment == env:
                    if getStoppedInst[account][env]:
                        patchGroupList, resGrp, ec2res, ec2client, ssmClient = getSession(account)
                        tableSratStopInst.append('<table>'
                                             '<tr>'
                                             '<td style="border:5px solid white;" colspan="3"> </td>'
                                             '</tr>'
                                             '<tr>'
                                             '<th style="background-color:#FFBB33" colspan="3">' + account + " " + env + " Stopped Instances" + '</th>'
                                                                                                                                                '</tr>')
                        for startPatchingCycleTag in getStoppedInst[account][env]:
                            tableSratStopInst.append(
                                '<tr>'
                                '<td style="text-align: center;" colspan="3"> <strong> PatchingCycle Tag: ' + startPatchingCycleTag + '</strong> </td>'
                                                                                                                                           '</tr>'
                                                                                                                                           '<tr>'
                                                                                                                                           '<th> <strong> Instance Id </strong> </th>'
                                                                                                                                           '<th> <strong> Instance Name </strong> </th>'
                                                                                                                                           '<th> <strong> Instance State </strong> </th>'
                                                                                                                                           '</tr>'
                            )
                            for instId, instName in getStoppedInst[account][env][startPatchingCycleTag].items():
                                inst = ec2res.Instance(instId)
                                print("Account:", account, "PatchingTag:", startPatchingCycleTag,
                                      "InstanceId:", instId, "InstanceName:", instName, "InstanceState:",
                                      inst.state['Name'])
                                tableSratStopInst.append(
                                    '<tr>'
                                    '<td>' + instId + '</td>'
                                                      '<td>' + instName + '</td>'
                                                                          '<td>' + inst.state['Name'] + '</td>'
                                                                                                        '</tr>'
                                )
        tableSratStopInst.append('</table>')
        tableSratStopInst.append('<h4> <i>Automated</i> </h4>')
        subject = f"Automated Patch {env}: Starting Instances On {str(datetime.now().date())}"
        bodyMessage = (''.join(tableSratStopInst))
        sendEmail(subject, bodyMessage, resourceConfig.toEmailList)

    if action == "StopInst":
        # Stop Instances
        # Get Data from S3
        getStoppedInst = getDataFromS3(reportCommand)
        for account in getStoppedInst:
            for environment in getStoppedInst[account]:
                if environment == env:
                    if getStoppedInst[account][env]:
                        patchGroupList, resGrp, ec2res, ec2client, ssmClient = getSession(account)
                        for stopPatchingTag in getStoppedInst[account][env]:
                            for instId, instName in getStoppedInst[account][env][stopPatchingTag].items():
                                # Main Stopping Instances after patch.
                                stopEc2Inst(ec2client, instId, env, account)

        # Buffer time for upload.
        time.sleep(5)
        # Get Data from S3
        for account in getStoppedInst:
            for environment in getStoppedInst[account]:
                if environment == env:
                    if getStoppedInst[account][env]:
                        patchGroupList, resGrp, ec2res, ec2client, ssmClient = getSession(account)
                        tableSratStopInst.append(
                            '<table>'
                            '<tr>'
                            '<td style="border:5px solid white;" colspan="3"> </td>'
                            '</tr>'
                            '<tr>'
                            '<th style="background-color:#FFBB33" colspan="3">' + account + " " + env + " Stopped Instances" + '</th>'
                                                                                                                               '</tr>'
                        )
                        for stopPatchingTag in getStoppedInst[account][env]:
                            tableSratStopInst.append(
                                '<tr>'
                                '<td style="text-align: center;" colspan="3"> <strong> PatchingCycle Tag: ' + stopPatchingTag + '</strong> </td>'
                                                                                                                                          '</tr>'
                                                                                                                                          '<tr>'
                                                                                                                                          '<td> <strong> Instance Id </strong> </td>'
                                                                                                                                          '<td> <strong> Instance Name </strong> </td>'
                                                                                                                                          '<td> <strong> Instance State </strong> </td>'
                                                                                                                                          '</tr>'
                            )
                            for instId, instName in getStoppedInst[account][env][stopPatchingTag].items():
                                inst = ec2res.Instance(instId)
                                tableSratStopInst.append(
                                    '<tr>'
                                    '<td>' + instId + '</td>'
                                                      '<td>' + instName + '</td>'
                                                                          '<td>' + inst.state['Name'] + '</td>'
                                                                                                        '</tr>')

        tableSratStopInst.append('</table>')
        tableSratStopInst.append('<h4> <i>Automated</i> </h4>')
        subject = f"Automated Patch {env}: Stopping Instances On {str(datetime.now().date())}"
        bodyMessage = (''.join(tableSratStopInst))
        sendEmail(subject, bodyMessage, resourceConfig.toEmailList)
