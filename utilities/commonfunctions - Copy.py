from unittest import TestCase
import pandas as pd
import configparser
import json
import os
import requests
import datetime 
import logging 
from utilities.logger import *

class CommonFunctions:

    # Gets Configurations from the property file 
    def getConfigProperty():
        config= configparser.ConfigParser()
        config.read('properties.ini')
        return config

    #Reads and outputs the content of the excel file
    def getExcelData(file, sheet):      
        dat_excel = pd.read_excel(file, sheet_name=sheet)
        dat_str = dat_excel.to_json(orient='records')        
        return dat_str
    
    # 11/04 Opens the json file and reads the content and returns json content in a dict valiable
    # take input as whole path of the file with file name
    #def getJson(file):
        #with open(file) as f:
            #json_struct =json.load(f)
        #return json_struct


    # Gets the base path and attaches the file path provided.
    # it take the folder to append to base path or the path with the file name to append to base
    def getFilePath(filename):
        dat_path= os.path.abspath(filename)
        return dat_path

   # Deletes the test result file. FilePath with Filename needs to be provided
    def clearReports(TestResultJsonFile):
        if os.path.exists(TestResultJsonFile):
            os.remove(TestResultJsonFile)
        else:
            "do nothing. File created"


    # Deletes all the files from the directory/folder provided.
    # takes the full path of directory.folder as input 
    def clearFileFromDir(dirPath):
        for f in os.listdir(dirPath):
            os.remove(os.path.abspath(os.path.join(dirPath,f)))
    
    # Gets the list if all the files in the directory/folder
    # takes the full path of the directory/folder as input
    def getFileFromDir(dirPath):
        files = []
        i=0
        for f in os.listdir(dirPath):
            f = os.path.abspath(os.path.join(dirPath,f))
            files.insert(i,f)
            i=i+1
        return files
    
    # 11/04 Gets only the filename and strips off the ".json" file extension. 
    # Takes full path of the file with filename as input
    def stripFileName(filePath):
        file = os.path.basename(filePath)
        filename = file [:len("json")]
        return filename
   
    # 11/04 Gets the folderpath and appends the testcase# as file name for displaying json payload response
    # takes the folder path and row of expected data from Input Excel file as input
    def createRespPayloadFilePath(row, path):
        TCId = row ['Testcase_No']
        TCFile= path+TCId+".json"
        return str(TCFile)
    
    #Reads and outputs the content of the Expected results from excel sheet
    def getExpectedOutput(expectedList, i, column):
        expectedList1=json.loads(expectedList)
        if(column=='Status'):
            df=pd.DataFrame(expectedList1)
            js_expected=df.iloc[i,1]
        if(column=='Body'):
            df=pd.DataFrame(expectedList1)
            js_expected_str=df.iloc[i,2]
            js_expected=json.loads(js_expected_str)
        return js_expected

    
    # Comparing response with Expected results
    def processJBody(resBody,expectedBody, validateFields, response,expectedStatus):
        #assertField = 'match' # 0=true and 1= false
        assertField={}
        results={}
        if (response==None):# requestpayload file is empty etc
            results["reason"] = expectedStatus 
        else:
            if (response.status_code  == expectedStatus):
                assertStatus = 'Response matching with expected value'
            else:
                expStatus= str(expectedStatus)
                respcode =  str(response.status_code)
                assertStatus = "expected:"+ expStatus + ", actual:"+ respcode
                results["error"] = assertStatus
    
        validateFields = validateFields.split(",")

        if (resBody == None):
            print("resbody is None. So no need to assert the fields")
        else:   
            for index, key in enumerate(validateFields):
                key = validateFields[index]
                if (resBody[key] == expectedBody[key]):
                    assertField = 'Response matching with expected value'
                else:   
                    respvalue = str(resBody[key])
                    expValue = str(expectedBody[key])
                    assertField = "expected:" + expValue + ", actual:"+ respvalue
                    results[key] = str(assertField)
        return results


    #assembles the Testcase results
    def buildTCResults(info, resultsJBody):
        finalObj={} # defining dict object for returning
        if (resultsJBody=={}):
            # testcases passed
            finalObj = {'ban':info['ban'],'TCId':info['TCId'],'TCDesc':info['TCDesc'],
            'startDttm':info['startDttm'],'endDttm':info['endDttm'],'executionTime':info['executionTime'],'status': "passed"}
        else:
            if('reason' in resultsJBody.keys() ):
                finalObj = {'ban':info['ban'],'TCId':info['TCId'],'TCDesc':info['TCDesc'],
                'startDttm':info['startDttm'],'endDttm':info['endDttm'],'executionTime':info['executionTime'],'mismatchFields':resultsJBody,
                'status': "skipped"}
            else:
                finalObj = {'ban':info['ban'],'TCId':info['TCId'],'TCDesc':info['TCDesc'],
                'startDttm':info['startDttm'],'endDttm':info['endDttm'],'executionTime':info['executionTime'],'mismatchFields':resultsJBody,
                'status': "failed"}

        return finalObj
    
    #prints the Testcase results to the result file
    def writeToJsonResultfile(file,testresult):
        testfile=open(file,'a')
        testcaseJ=json.dumps(testresult,indent=4)
        testfile.write(testcaseJ)
        testfile.close()
    
    #generating token
    def getToken(url,username, password):
        try:
            response = requests.post(url, auth=(username, password))
            resp=response.json()
            token= resp['access_token']
            return token
        except BaseException as err:
            print(f"Unexpected {err=}, {type(err)=}")
    
    # returns the datetime 
    def getDateTime():
        dtTime = datetime.datetime.utcnow()
        val = str(datetime.datetime.strftime(dtTime, "%Y-%m-%d %H:%M:%S"))
        return val

    # returns the date only in format eg 2022-11-01
    def getDate():
        dtTime = datetime.datetime.utcnow()
        val = str(datetime.datetime.strftime(dtTime,"%Y-%m-%d"))
        return val

    # calculates the execution time
    def getExecutionTime(startDttm, endDttm):
        executionTime= int(round((endDttm-startDttm).total_seconds() * 1000.0))
        return executionTime


    #Opens the json file and reads the content and returns json content in a dict variable
    # takes input of dirrector path where the JSON payload files reside, testcase_no and BAN from excel file
    def getJson(dirPath,fname,exlBan ):
        i=0
        fname = fname+".json"
        val=False
        for f in os.listdir(dirPath):
            # Check if the json payload file exists in the directory
            if (f == fname): # file exists 
                file = os.path.abspath(os.path.join(dirPath,f))
                val = True
                break
            else:          
                val= False
                i=i+1 # if not then loop through to see if it exists
        
        if (val== False):
            #log= Logger.logger('commonfunctions')
            logging.error ("File "+fname +" is not in directory "+dirPath)
        
        # Check if json payload file is not empty
        if (val==True):
            if (os.path.getsize(file) > 0):
                with open(file) as f:
                    json_struct =json.load(f)
                val = True
            else:
                val= False 
                logging.error ("File "+fname +" is empty")
        
        # Check if the json file is for the correct ban
        if (val==True):
            if (json_struct ["request"]["body"]["coreAcctBan"] == exlBan):   
                return json_struct  # expected Ban matches the Ban in the json payload file
            else:
                val = False
                logging.error("Jsonfile " +fname + "content does not belong to expected ban")
        else:
            json_struct = None  # if not then send empty variable
            return json_struct


    



    

    
    




    


    









    

    
