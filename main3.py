from stage1 import stage1
#from stage2 import stage2
from stage_edit import stage_edit
from funcs.browserFuncs import *
from pykeepass import PyKeePass

headers = { 'Authorization' : 'Basic cm9ib3Q6cm9ib3RfMTIz'}
kp = PyKeePass('C:\KeePass\Database.kdbx', password='!mYP3TD=txAcb(Cr')
elnurId = '78671'
#TestId: 78534
testId = '78642'  
repSavePath = r"C:\EOKNO_temp"
rep = False


def debugJsonData(elnurId, headers):
    c = requests.get('http://cloud.ipcs.kz:60180/restapi/services/run/getReqInfo?id=' + elnurId, headers=headers)
    tData = c.text
    #print(tData)
    jsonData = json.loads(tData)
    debugJsonData = json.dumps(jsonData, ensure_ascii=False).encode('utf8')
    print(debugJsonData.decode())


#Прогнать первый этап
#Тест
print("---------------------------------------")
print("")
print("")
if rep == False:
    debugJsonData(testId, headers)
    print("----------------")
    stage1(elnurId, headers, kp, repSavePath)
    #stage_edit(testId, headers, kp, repSavePath)


if rep == True:
    repExtension = 'pdf'
    tId = '3206900'
    elnStatus2 = 'templ_approval'
    tFPath = os.path.join(repSavePath, 'new')
    resPath = os.path.join(tFPath, 'report_' + tId + '.' + repExtension)
    #print("prepared file for upload: " + resPath)
    res = uploadElnurFile(resPath)
    fileGuid = res["guid"]
    res = sendElnurStatus(elnStatus2, elnurId, tId, fileGuid)
#print(res)
#print("Alternative file")
#resPath = os.path.join(tFPath, 'report_3205642.pdf')
#res = uploadElnurFile(resPath)
#print(res)


#debugSetEoknoNum(elnurId, '3201763')
#stage2(elnurId, headers, kp, repSavePath)
#repExtension = 'pdf'
#tId = '3202484'
#tFPath = os.path.join(repSavePath, 'new')
#resPath = os.path.join(tFPath, 'report_' + tId + '.' + repExtension)
#res = uploadElnurFile(resPath)
#print(res["result"])

#stageTest(elnurId, headers, kp, repSavePath)