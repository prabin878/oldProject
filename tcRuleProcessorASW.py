from datetime import datetime, timedelta
#from email.utils import localtime
#from genericpath import exists
from logging import error
import requests
from time import time
import json
from utilities.commonfunctions import*
import logging

resultslist=[ ] # list variable to hold results
testResults={} # dict variable to hold results
summary={}
totRecordsProcessed=0 #int to store number of records processed
totTCFailed=0
totTCPassed=0
totTCSkipped=0
JFiles =[] # list variable to hold the request files from datafiles folder

#generating logs
log=CommonFunctions.getConfigProperty()['LOG']['logs']
logpath=CommonFunctions.getFilePath(log)
logging.basicConfig(filename=logpath, filemode='w', encoding='utf-8',
  level=logging.DEBUG,format='%(levelname)s -%(asctime)s -{%(module)s %(funcName)s:%(lineno)d} - %(message)s', datefmt='%m/%d/%Y%I:%M:%S %p')

#Get (Summary ) inital Test processing information like starttime etc to populate in Report
summary['startDttm'] = str(CommonFunctions.getDateTime()) # Start date and time for file exec to display in report 
print ("startdttime"+ summary['startDttm'])
totStartTime=datetime.datetime.now() # capture current start time to calculate total exec time later
summary['microServiceName']= "Rule-Processor ASW"
summary['date'] = str(CommonFunctions.getDate())

# Getting URL from property file
baseURL = CommonFunctions.getConfigProperty()['API']['baseUrlRp']
resURL = CommonFunctions.getConfigProperty()['API']['apiRuleProcessorAsw']
URL= baseURL + resURL

# Get path of the Input excel file from property file
rpDatFileName=CommonFunctions.getConfigProperty() ['INPUTFILE']['inputFileRpAsw']
reqFilePath=CommonFunctions.getFilePath(rpDatFileName)

#Get path of the Request Payload (Input JSON Request) folder from property file
requestJFile=CommonFunctions.getConfigProperty() ['INPUTFILE']['inputJsonFileAsw']
requestJFile=CommonFunctions.getFilePath(requestJFile)

# remove files from response payload
filePath= CommonFunctions.getConfigProperty() ['TESTCASERESULTS'] ['tcrRpAswResponsePayload']
CommonFunctions.clearFileFromDir(filePath)

# Get the content from the Input excel file
dat_str=CommonFunctions.getExcelData(reqFilePath,"Request")
dat_list=json.loads(dat_str)

i=0 # variable to increment the rows in the request and expected excel sheets

# Get the result file name and path from the property file and calling function to delete previous report
ReportFilePath=CommonFunctions.getConfigProperty()['TESTCASERESULTS']['tcrRpAsw']
ReportFilePath= CommonFunctions.getFilePath(ReportFilePath)
CommonFunctions.clearReports(ReportFilePath)

# Getting fields that needs to be validated from property file
validateFields= CommonFunctions.getConfigProperty()['VALIDATEFIELDS']['vfRpAsw']

# Get token and pass it to header
tkURL=CommonFunctions.getConfigProperty()['TOKEN']['apigeeURL']
tkuser= CommonFunctions.getConfigProperty()['TOKEN']['apigeeUser']
tkpwd= CommonFunctions.getConfigProperty()['TOKEN']['apigeePwd']
token=CommonFunctions.getToken(tkURL,tkuser,tkpwd)
header = {'Content-Type': 'application/json','Authorization':'Bearer '+ token}


# Iterating through the Request rows from the Input file, passing it to API and comparing with Expected output
for row in dat_list:
    try:
        info = {} # dict for storing below information from request tab of excel sheet
        singleJTestcase = {} # for storing the results of the testcase
        
        # Get Testcase execution start time
        executionStartTime=CommonFunctions.getDateTime()
        startt=datetime.datetime.now()

        # Information from request data that needs to be populated in test result
        info['ban'] = row ['coreAcctBan']
        #info['rNo'] = row ['Serial_No']
        info['TCId'] = row ['Testcase_No']
        info['TCDesc'] = row ['Testcase_Desc']
        info['startDttm'] = executionStartTime #Testcase execution start time
        expConvId= row ['conversionId']
        
        if (expConvId ==None):
            expConvId ="" 
       
        # Get the json content for Request and Expected Response payload from the JSON Payload file
        tcno= row ['Testcase_No']
        ban= row ['coreAcctBan']
        jsom_struct= []
        json_struct= CommonFunctions.getJson(requestJFile,tcno,ban)
        if json_struct != None : # Check if the file present and not empty or ban matches
            json_req = json_struct ["request"]
            exp_resp = json_struct ["response"]
            json_data = json_struct ["request"]["body"]
            expectedStatus = row ['expRespStatus']   # Get expected status code from the input excel file
            payloadConvId = json_struct ["request"]["body"]["conversionId"]

            isValidConv = CommonFunctions.processPayloadConversionId(payloadConvId,expConvId)
            if (isValidConv == True):
                # Making API request
                js=json.dumps(json_data)
                try:
                    rs = requests.post(URL,js,headers=header,verify=False)
                except requests.exceptions.RequestException as err:
                    logging.exception(err)

                # Check API status is pass or fail 
                result = CommonFunctions.processAPIStatus(rs, expectedStatus)
                   
                if ('apiPass' in result.keys()):
                    resBody = rs.json()
                    # Get api response for each testcase in a file and write to the file in responsepayload folder
                    TCfile = CommonFunctions.createRespPayloadFilePath(row,filePath)
                    TCfile= CommonFunctions.getFilePath(TCfile)
                    CommonFunctions.writeToJsonResultfile (TCfile,resBody)

                    #Check if Expected ResponseBody from Payload file is empty or not
                    expRespBodyBlank= CommonFunctions.processPayloadExpRespBodyEmpty(resBody,exp_resp)

                    if (expRespBodyBlank!=True): # expected ResponseBody NOT blank
                     # Comparing the response with the expected result
                        resultsJBody = CommonFunctions.processPayloadFields(resBody, exp_resp, validateFields)
                    else:
                    # Expected payload is blank in payload file, But expected status code from excel matches actual status code
                    # Then mark testcase as passed as expectedStatus same as actual status...do nothing
                        resultsJBody = {}
    
                    print("************************ Test Case Result ***********************************")
                    print("RESPONSE Data: " + str(rs.status_code) + " **********" + str(resBody))
                    print("EXPECTED Data: :" + str(expectedStatus) + " **********" + str(exp_resp))
                else: # API status does not match with expected status. ie API fail
                    resultsJBody = result
            else:# Conversion id is either blank or not matching with expectedConversionId
                logging.error (tcno +":JSON file for "+str(ban)+"- verify conversion id in file")
                json_struct= None
                result= CommonFunctions.processPayloadFileError(json_struct, tcno, ban)
                resultsJBody = result
        else: # executes when there is some error with the RequestPayload file
            logging.error (tcno +":JSON file for "+str(ban)+"- either file does not exist or is blank or has invalid json or ban/conversion id is not matching")
            result= CommonFunctions.processPayloadFileError(json_struct, tcno, ban)
            resultsJBody = result
 
        # Get Test case execution end time 
        info['endDttm']=str(CommonFunctions.getDateTime())
        endt=datetime.datetime.now()
        info['executionTime'] = CommonFunctions.getExecutionTime(startt,endt)

        # combining together the expected TC info and the results
        singleJTestcase = CommonFunctions.buildTCResults(info,resultsJBody)
        resultslist.insert(i,singleJTestcase)

        if singleJTestcase['status'] =='failed':
            totTCFailed=totTCFailed+1
        else:
            if singleJTestcase['status'] =='passed':
                totTCPassed=totTCPassed+1
            else:
                totTCSkipped=totTCSkipped+1
        
            print("*******************************************************************************")
            totRecordsProcessed = totTCFailed + totTCPassed + totTCSkipped
        i=i+1  #increments to the next testcase data
        
    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)}, {err.__doc__} {err}")
        logging.error(err)
       
    
# Get End of processing time and append Testcases results to populate in Reports
totEndTime = datetime.datetime.now() # total test execution end time
summary['endDttm'] =  CommonFunctions.getDateTime() # total test execution end date time
summary['executionTime'] = CommonFunctions.getExecutionTime(totStartTime,totEndTime) # storing total execution time
summary['totalRec'] = totRecordsProcessed
summary['passed'] = totTCPassed
summary['failed'] = totTCFailed
summary['skipped'] = totTCSkipped
testResults['summary']= summary
testResults['results']= resultslist # append test results of each Testcases

# Write all of the test results to the file 
CommonFunctions.writeToJsonResultfile (ReportFilePath,testResults)
    
    
   

    
      


   
    
