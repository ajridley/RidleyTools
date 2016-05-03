##MetadataUpdate.py
##Created Spring 2016 by Adam Ridley, GIS Specialist
##Cottonwood Field Office - Bureau of Land Management
##This script provides functionality exports and tests the currency of metadata between 
##local field office replicas and the IDP1V database in SDE. Local metadata which appears
##out of date can be replaced, if so desired.
##This script relies on the AddMsg module to function properly.

import os
import sys
import arcpy
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime
from AddMsg import AddMsgAndPrint

## Set variables
#SDE connection settings
sdeFolderName = r"c:\tmp\connectionFiles"
sdeFileName = "TempIDP1V.sde"
databasePlatform = "SQL_SERVER"
instance = "ILMIDSO3DB3"
database = "IDP1V"
acc_auth = "OPERATING_SYSTEM_AUTH"
#Output folder and file settings
localDB = r"R:\loc\GIS\SDE_Master_Data\SDE_PROJECTED_FGDB.gdb"
sdeMetaFolder = r"R:\loc\GIS\MISC_SUPPORT\Metadata\SDE_Converted"
localMetaFolder = r"R:\loc\GIS\MISC_SUPPORT\Metadata\Local_Converted"
logStub = r"R:\loc\GIS\MISC_SUPPORT\Metadata\ScriptLog_"
sdePrefix = "IDP1V.IDSD1."
replaceLocal = sys.argv[1] #Boolean Input Parameter

## Function which creates a connection to IDP1V, walks through the datasets therein, and copies unaltered metadata from those datasets to local files
def ExportSDEMetadata():
	AddMsgAndPrint("Exporting SDE metadata...")
	# Create a temporary workspace to house SDE connection file
	sde_workspace = os.path.join(sdeFolderName,sdeFileName)
	if not os.path.exists(sdeFolderName):
		os.makedirs(sdeFolderName)
	if not os.path.exists(sdeMetaFolder):
		os.makedirs(sdeMetaFolder)
	# Create connectionfile for IDP1V
	if not os.path.exists(sde_workspace):
		result = arcpy.CreateDatabaseConnection_management (sdeFolderName,sdeFileName,databasePlatform,instance,acc_auth,database = "IDP1V")
	AddMsgAndPrint("Connecting to IDP1V")

	# Walk through IDP1V connection
	walk = arcpy.da.Walk(sde_workspace,followlinks = True,datatype = ['Table', 'FeatureClass'])
	AddMsgAndPrint("Walk complete: " + str(datetime.now()))
	# For each dataset, create an dummy xml file and use the Metadata Importer to create a non-translated version of the files current metadata
	for dirpath,dirnames,filenames in walk:
		for file in filenames:
			CreateXML(dirpath,file,sdeMetaFolder)
			AddMsgAndPrint(file)
	
## Function which walks through local SDE replica and calls CreateXML
def ExportLocalMetadata():
	AddMsgAndPrint("Exporting local metadata...")
	# Make sure localMetaFolder exists
	arcpy.env.overwriteOutput = True
	if not os.path.exists(localMetaFolder):
		os.makedirs(localMetaFolder)
	# Walk through local replica and call Create
	walk = arcpy.da.Walk(localDB)
	AddMsgAndPrint("Walk complete: " + str(datetime.now()))
	for dirpath,dirnames,filenames in walk:
		for file in filenames:
			CreateXML(dirpath,file,localMetaFolder)
			AddMsgAndPrint(file)

## Function to create dummy XML and import untranslated metadata to file
def CreateXML(dirpath,file,metaFolder):
	metaFile = os.path.join(metaFolder,file + ".xml")
	with open(metaFile, 'w') as f:
		f.write("<metadata />")
		f.close()
	try:
		arcpy.MetadataImporter_conversion (os.path.join(dirpath,file),metaFile)
	except:
		AddMsgAndPrint(arcpy.GetMessages())
				
## Function which finds and compares equivalent metadata files to determine which is more recently updated via the ModDate element			
def TestMetadata():
	# Create dicts to hold names/dates for comparison
	sdeDates = {}
	localDates = {}
	# Create lists to hold the compare results
	sdeCurrent = []
	localCurrent = []
	troubleData = []
	sdeFiles = [f for f in os.listdir(sdeMetaFolder) if os.path.isfile(os.path.join(sdeMetaFolder, f))] # Gather and process SDE metadata files
	for file in sdeFiles:
		# Test to make sure the given file in an XML
		if file[-4:] == ".xml":
			sdeTree = ET.parse(os.path.join(sdeMetaFolder,file))
			root = sdeTree.getroot()
			sdeElement = root.find("./Esri/ModDate")
			if ET.iselement(sdeElement):
				sdeDates[file.replace(sdePrefix, "")] = sdeElement.text # Add "name: mod date" pair to SDE dict
			else:
				AddMsgAndPrint(file + " does not contain a ModDate")
	localFiles = [f for f in os.listdir(localMetaFolder) if os.path.isfile(os.path.join(localMetaFolder, f))] # Gather and process local metadata files
	for file in localFiles:
		# Test to make sure the given file in an XML
		if file[-4:] == ".xml":
			localTree = ET.parse(os.path.join(localMetaFolder,file))
			root = localTree.getroot()
			localElement = root.find("./Esri/ModDate")
			if ET.iselement(localElement):
				localDates[file] = localElement.text  # Add "name: mod date" pair to local dict
			else:
				troubleData.append(file[:-4])
				AddMsgAndPrint(file + " does not contain a ModDate")
	# Compare dates from equivalent named datasets and add to appropriate list for output
	for key in localDates.iterkeys():
		if key in sdeDates:
			if int(sdeDates[key]) > int(localDates[key]):
				sdeCurrent.append(key)	
			elif int(sdeDates[key]) <= int(localDates[key]):
				localCurrent.append(key)
		else:
			AddMsgAndPrint(key + " has no matching feature class")
	if replaceLocal == True:
		for dirpath, dirnames, filenames in arcpy.da.Walk(localDB):
			for file in filenames:
				if file in sdeCurrent:
					importFile = os.path.join(sdeMetaFolder, (sdePrefix + file))
					arcpy.MetadataImporter_conversion (importFile, os.path.join(dirpath,file))
	logFile = logStub + startTime.strftime("%Y%m%d") + ".txt"
	with open(logFile, 'w') as f:
		f.write(str(len(localCurrent)) + " features with current Metadata locally:\n\n")
		for x in localCurrent:
			f.write(x + "\n")
		f.write("\n")
		f.write(str(len(sdeCurrent)) + " features with current Metadata in SDE:\n\n")
		for y in sdeCurrent:
			f.write(y + "\n")
		f.write("\n")
		f.write(str(len(troubleData)) + " features without a mod date or matching feature class:\n\n")
		for z in troubleData:
			f.write(z + "\n")
		f.close()
	AddMsgAndPrint("Results available at: " + logFile)

## Main script execution statement
try:
	startTime = datetime.now()
	AddMsgAndPrint("Start Time: " + str(startTime))
	arcpy.env.overwriteOutput = True
	ExportSDEMetadata()
	ExportLocalMetadata()
	TestMetadata()
			
except:
	# Print error message if an error occurs
	AddMsgAndPrint(arcpy.GetMessages())
	AddMsgAndPrint("Failure at: " + str(datetime.now()))
	AddMsgAndPrint("Unexpected error: ", sys.exc_info()[0])
	AddMsgAndPrint(traceback.print_exc())
	
finally:
	#os.remove(os.path.join(sdeFolderName,sdeFileName))
	AddMsgAndPrint("Script execution: " + str(datetime.now()-startTime))
