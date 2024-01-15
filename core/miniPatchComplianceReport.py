from config import resourceConfig
from library.globalComponent import sendEmail, getSession, getTag
from datetime import date
from datetime import datetime

today_day = date.today()
tableMiniPatchCompliance = ['<html>'
                            '<head><style>table {font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;border-collapse: collapse; } '
                            'td,th{'
                            'border:1px solid #ddd;'
                            'padding:8px;'
                            'width:1%;'
                            '}'
                            '</style>''</head>',
                            '<h2 align="center"><u>\n\n</u></h2><body>']


def generateMiniPatchComplianceReport(accountProfile, env):
    tableMiniPatchCompliance.append('<table>'
                                    '<tr>'
                                    '<td style="border:5px solid white;" colspan="8"> </td>'
                                    '</tr>'
                                    '<tr>'
                                    '<th style="background-color:#FFBB33" colspan="8">' + env + " Mini Patch Compliance Report" + '</th>'
                                      '</tr>'
                                      '<tr>'
                                      '<td> <strong> Account </strong> </td>'
                                      '<td> <strong> ResourcePatchGroup </strong> </td>'
                                      '<td> <strong> InstanceId </strong> </td>'
                                      '<td> <strong> InstanceName </strong> </td>'
                                      '<td> <strong> Baseline </strong> </td>'
                                      '<td> <strong> LastPatchDate </strong> </td>'
                                      '<td> <strong> CountDays </strong> </td>'
                                      '<td> <strong> Status </strong> </td>'
                                      '</tr>'
                                    )
    for account in accountProfile:
        patchResourceGroupList, resGrp, ec2res, ec2client, ssmClient = getSession(account)
        getSessionPatchPaginator = ssmClient.get_paginator('describe_instance_patches')
        # Get Resources Group
        for patchResourceGroup in patchResourceGroupList[env]:
            resFromResources = resGrp.list_group_resources(
                Group=patchResourceGroup,
            )
            # Get EC2 Resources From Resource Group
            for resources in resFromResources['Resources']:
                instId = resources['Identifier']['ResourceArn'].split("/")[-1]
                instName = getTag(ec2res, instId, "Name")
                try:
                    getInstDescribePatchDatePaginator = getSessionPatchPaginator.paginate(
                        InstanceId=instId,
                    )
                    getInstPatchStateForBaseline = ssmClient.describe_instance_patch_states(
                        InstanceIds=[
                            instId,
                        ],
                    )
                    baseLineName = ""
                    # Get Ec2 Resources Patch baseline
                    for getInstBaseline in getInstPatchStateForBaseline['InstancePatchStates']:
                        describeBaseline = ssmClient.describe_patch_baselines()
                        for baseline in describeBaseline['BaselineIdentities']:
                            if baseline['BaselineId'].split("/")[-1] == str(getInstBaseline['BaselineId']):
                                baseLineName = baseline['BaselineName']
                    instPatchDateList = []
                    # Condition if Windows "KB2267602" and Linux "amazon-"
                    for getInstPatchDate in getInstDescribePatchDatePaginator:
                        for getPatch in getInstPatchDate['Patches']:
                            if getPatch['State'] == "Installed" or getPatch['State'] == "InstalledPendingReboot" or \
                                    getPatch['State'] == "InstalledOther":
                                if "amazon-" not in getPatch['KBId'] and "KB2267602" not in getPatch['KBId']:
                                    instPatchDateList.append(getPatch['InstalledTime'].date())
                    instPatchDateList = list(dict.fromkeys(instPatchDateList))
                    countPatchDay = today_day - sorted(instPatchDateList)[-1]
                    if countPatchDay.days > 60:
                        print(account, patchResourceGroup, instId, instName, baseLineName,
                              sorted(instPatchDateList)[-1],
                              countPatchDay.days, "NotCompliant")
                        # Table append for NotCompliant
                        tableMiniPatchCompliance.append(
                            '<tr style="background-color:#FA5B39">'  # Red
                            '<td>' + account + '</td>'
                            '<td>' + patchResourceGroup + '</td>'
                            '<td>' + instId + '</td>'
                            '<td>' + instName + '</td>'
                            '<td>' + baseLineName + '</td>'
                            '<td>' + str(sorted(instPatchDateList)[-1]) + '</td>'
                            '<td>' + str(countPatchDay.days) + '</td>'
                            '<td>NotCompliant</td>'
                            '</tr>'
                        )
                    elif countPatchDay.days > 50:
                        print(account, patchResourceGroup, instId, instName, baseLineName,
                              sorted(instPatchDateList)[-1],
                              countPatchDay.days, "Warning")
                        # Table append for Warning
                        tableMiniPatchCompliance.append(
                            '<tr>'  # Yellow
                            '<td>' + account + '</td>'
                            '<td>' + patchResourceGroup + '</td>'
                            '<td>' + instId + '</td>'
                            '<td>' + instName + '</td>'
                            '<td>' + baseLineName + '</td>'
                            '<td>' + str(sorted(instPatchDateList)[-1]) + '</td>'
                            '<td>' + str(countPatchDay.days) + '</td>'
                            '<td style="background-color:#FCFF33" >Warning</td>'
                            '</tr>'
                        )
                    else:
                        print(account, patchResourceGroup, instId, instName, baseLineName,
                              sorted(instPatchDateList)[-1],
                              countPatchDay.days, "Compliant")
                        # Table append for Compliant
                        tableMiniPatchCompliance.append(
                            '<tr>'  # Green
                            '<td>' + account + '</td>'
                            '<td>' + patchResourceGroup + '</td>'
                            '<td>' + instId + '</td>'
                            '<td>' + instName + '</td>'
                            '<td>' + baseLineName + '</td>'
                            '<td>' + str(sorted(instPatchDateList)[-1]) + '</td>'
                            '<td>' + str(countPatchDay.days) + '</td>'
                            '<td style="background-color:#61FF33" >Compliant</td>'
                            '</tr>'
                        )
                except Exception as e:
                    print(e)
                    print(account, patchResourceGroup, instId, instName, "NoData", "NoData",
                          "NoData", "NoData")
                    # Table append for "No Data"
                    tableMiniPatchCompliance.append(
                        '<tr style="background-color:#FA5B39">'  # Red
                        '<td>' + account + '</td>'
                        '<td>' + patchResourceGroup + '</td>'
                        '<td>' + instId + '</td>'
                        '<td>' + instName + '</td>'
                        '<td>NoData</td>'
                        '<td>NoData</td>'
                        '<td>NoData</td>'
                        '<td>NoData</td>'
                        '</tr>'
                    )

    tableMiniPatchCompliance.append('</table>')
    tableMiniPatchCompliance.append('<h4> <i>Automated</i> </h4>')
    subject = f"Automated Patch {env}: Mini Compliance Report On {str(datetime.now().date())}"
    bodyMessage = (''.join(tableMiniPatchCompliance))
    sendEmail(subject, bodyMessage, resourceConfig.toEmailList)