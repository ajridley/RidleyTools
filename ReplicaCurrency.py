##ReplicaCurrency.py
##Created Spring 2016 by Adam Ridley, GIS Specialist
##Cottonwood Field Office - Bureau of Land Management
##This script provides functionality etests the currency of data between 
##local field office replicas and the IDP1V database in SDE. Local data 
##which appears out of date can be replaced, if so desired.
##This script relies on the AddMsg module to function properly.

import os
import sys
import arcpy
import traceback
from datetime import datetime
from AddMsg import AddMsgAndPrint

# Set variables
sdeFolderName = r"c:\tmp\connectionFiles"
sdeFileName = "TempIDP1V.sde"
sdePrefix = "IDP1V.IDSD1."
databasePlatform = "SQL_SERVER"
instance = "ILMIDSO3DB3"
database = "IDP1V"
acc_auth = "OPERATING_SYSTEM_AUTH"
localDB = r"R:\loc\GIS\SDE_Master_Data\SDE_PROJECTED_FGDB.gdb"
sdeCurrent = []
localCurrent = []
matchingLayers = []
noEquivalent = []
detailed = False #sys.argv[1]
replaceLocal = False #sys.argv[2]
logStub = r"R:\loc\GIS\SDE_Master_Data\ReplicaCurrencyLog_"

try:
	startTime = datetime.now()
	AddMsgAndPrint("Start Time: " + str(startTime))
	sde_workspace = os.path.join(sdeFolderName,sdeFileName)
	if not os.path.exists(sdeFolderName):
		os.makedirs(sdeFolderName)
	# Create connectionfile for IDP1V in a temp workspace
	if not os.path.exists(sde_workspace):
		result = arcpy.CreateDatabaseConnection_management (sdeFolderName,sdeFileName,databasePlatform,instance,acc_auth,database = "IDP1V")
	AddMsgAndPrint("start connection")
	
	#Walk through IDP1V connection
	AddMsgAndPrint(sde_workspace)
	walk = arcpy.da.Walk(sde_workspace,followlinks = True,datatype = ['Table', 'FeatureClass'])  #Limit walk to tables and feature classes
	AddMsgAndPrint("Walk complete: " + str(datetime.now()))
	for dirpath,dirnames,filenames in walk:
		for file in filenames:
			fcName = file.replace(sdePrefix,"") #Removes the IDP1V.IDSD1. prefix from the filename
			print fcName
			fdName = dirpath[37:].replace(sdePrefix,"")
			if fdName != "":
				print fdName
				localDirPath = os.path.join(localDB,fdName) #Adds the feature dataset to the path, if there is one
				localPath = os.path.join(localDirPath,fcName) #Creates the local path by joining the file name to the conditioned local directory path
			else:
				localPath = os.path.join(localDB,fcName)
			print localPath
			if arcpy.Exists(localPath): #Test to make sure the local path references an existing dataset
				sdePath = os.path.join(dirpath,file)
				#Test for level of comparison
				if detailed == False:
					#Retrieve and test feature counts; update lists 
					result = arcpy.GetCount_management(sdePath)
					sdeCount = int(result.getOutput(0))
					result = arcpy.GetCount_management(localPath)
					localCount = int(result.getOutput(0))
					if sdeCount > localCount:
						sdeCurrent.append(fcName)
						AddMsgAndPrint(fcName + " SDE count higher by " + str(sdeCount-localCount) + " features")
						if replaceLocal == True:
							arcpy.env.overwriteOutput = True
							arcpy.CopyFeatures_management(sdePath,localPath)
					elif sdeCount < localCount:
						localCurrent.append(fcName)
						AddMsgAndPrint(fcName + " local count higher by " + str(localCount-sdeCount) + " features")
					elif sdeCount == localCount:
						matchingLayers.append(fcName)
						AddMsgAndPrint(fcName + " counts equal. Nothing to see here. Move along.")
				else:
					DetailedCompare(sdePath,localPath) #Calls the FeatureCompare or TableCompare function - Currently indadvisable
			else:
				noEquivalent.append(fcName)
				AddMsgAndPrint(fcName + " does not have a local equivalent")
	#Setup and create log file
	logFile = logStub + startTime.strftime("%Y%m%d") + ".txt"
	with open(logFile, 'w') as f:
		if detailed == False:	
			f.write(str(len(matchingLayers)) + " datasets with equal feature counts:\n\n")
			for w in matchingLayers:
				f.write(w + "\n")
			f.write(str(len(localCurrent)) + " datasets with more features in the local replica:\n\n")
			for x in localCurrent:
				f.write(x + "\n")
			f.write("\n")
			f.write(str(len(sdeCurrent)) + " datasets with more features in IDP1V:\n\n")
			for y in sdeCurrent:
				f.write(y + "\n")
		f.write(str(len(noEquivalent)) + " datasets in IDP1V with no local equivalent:\n\n")
		for z in noEquivalent:
			f.write(z + "\n")
		f.close()
	AddMsgAndPrint("Results available at: " + logFile)
	
	os.remove(sde_workspace) #clean up temporary workspace/file with SDE Connection
	AddMsgAndPrint("Script execution: " + str(datetime.now()-startTime))

except:
	# Print error message if an error occurs
	os.remove(os.path.join(sdeFolderName,sdeFileName)) #clean up temporary workspace/file with SDE Connection
	AddMsgAndPrint(arcpy.GetMessages())
	AddMsgAndPrint("Failure at: " + str(datetime.now()))
	AddMsgAndPrint("Unexpected error: ", sys.exc_info()[0])
	AddMsgAndPrint(traceback.print_exc())

def DetailedCompare(sdePath,localPath):
	##Function to provide a more detail comparison mechanism using Feature/Table Compare
	desc = arcpy.Describe(sdePath)
	if hasattr(desc, "dataType"):
		#Find a field to sort for comparison purposes
		sortField = ""
		if desc.hasOID:
				sortField = desc.OIDFieldName
		for field in desc.fields:
			if field.name == "GlobalID":
				sortField = "GlobalID"
		try:
			#Perform Table or Feature Compares depending on dataType
			if desc.dataType == "Table":
				table_result = arcpy.TableCompare_management(in_base_table = sdePath, in_test_table = localPath, sort_field = sortField, compare_type = "ATTRIBUTES_ONLY",continue_compare = "NO_CONTINUE_COMPARE")
				AddMsgAndPrint(table_result.getOutput(1))
			
			elif desc.dataType == "FeatureClass":
				fc_result = arcpy.FeatureCompare_management(in_base_features = sdePath, in_test_features = localPath, sort_field = sortField, compare_type = "ATTRIBUTES_ONLY",ignore_options = ["IGNORE_M","IGNORE_Z"],continue_compare = "NO_CONTINUE_COMPARE")
				AddMsgAndPrint(fc_result.getOutput(1))
		except:
			AddMsgAndPrint("Compare error")
			AddMsgAndPrint(traceback.print_exc())