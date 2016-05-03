##ReportBrokenMXDs.py
##Created Spring 2016 by Adam Ridley, GIS Specialist
##Cottonwood Field Office - Bureau of Land Management
##This script provides functionality that tests MXDs for broken links and  
##reports them back to the user.  The script provides options run in Quiet
##mode and/or repair broken links for which it can find a match.
##This script relies on the AddMsg module to function properly.

import os
import sys
import arcpy
from datetime import datetime
from AddMsg import AddMsgAndPrint
import traceback

input = sys.argv[1]
brknNum = int(0)
totalFiles = int(0)
startTime = datetime.now()
Quiet = sys.argv[2]
FixSource = sys.argv[3]

def TestMXD(fullpath, Quiet, FixSource, logFile):
	##Function to test and create a report for any given MXD
	from FixLinks import SortPath
	global brknNum, totalFiles
	mxdTotal = int(0)
	mxd = arcpy.mapping.MapDocument(fullpath)
	#Create lists to contain output
	troubleLayers = []
	fixLayers = []
	noMatchLayers = []
	try:
		#Test for broken links and iterate through broken items
		brknItems = arcpy.mapping.ListBrokenDataSources(mxd)
		for brknItem in brknItems:
			foundPath = None
			#Test for dataSource property and pass to SortPath
			if hasattr(brknItem, "dataSource"):
				arcpy.AddMessage("Broken source path: " + brknItem.dataSource)
				foundPath = SortPath(brknItem.dataSource,Quiet)
			#Test for workspace path in absence of dataSource and pass to SortPath
			elif hasattr(brknItem, "workspacePath"):
				print "Workspace path exists"
				foundPath = SortPath(brknItem.workspacePath,Quiet)
			#Tell us what this troublesome data is
			else:
				AddMsgAndPrint("Datasource absent")
				troubleLayers.append(brknItem)
				desc = arcpy.Describe(brknItem)
				if hasattr(desc, "dataType"):
					AddMsgAndPrint(desc.datatype)
			#Parse results returned from SorthPath
			if foundPath == "No match":
				noMatchLayers.append(brknItem.dataSource)
			elif foundPath == "U: drive" or foundPath == "Q: drive":
				troubleLayers.append(brknItem.dataSource)
			elif foundPath != None:
				fixLayers.append(foundPath)
				if FixSource == True:
					brknItem.replaceDataSource(foundPath, "NONE",'#',validate = True)
			mxdTotal += 1
			brknNum += 1
		totalFiles += 1
		#Create or add to log file results
		with open(logFile, 'a') as f:
			if len(brknItems) == 0:
				AddMsgAndPrint("No Broken links in: " + fullpath)
				f.write("No Broken links in: " + fullpath + "\n\n")
			else:
				AddMsgAndPrint(str(mxdTotal) + " links broken in " + fullpath)
				f.write(str(mxdTotal) + " links broken in " + fullpath + "\n\n")
				AddMsgAndPrint(str(len(fixLayers)) + " fixable layers")
				f.write(str(len(fixLayers)) + " fixable layers\n\n")
				for x in fixLayers:
					f.write(x + "\n")
				f.write("\n")
				AddMsgAndPrint(str(len(noMatchLayers)) + " unmatchable layers")
				f.write(str(len(noMatchLayers)) + " unmatchable layers\n\n")
				for y in noMatchLayers:
					f.write(y + "\n")
				f.write("\n")
				AddMsgAndPrint(str(len(troubleLayers)) + " trouble layers")
				f.write(str(len(troubleLayers)) + " trouble layers\n\n")
				for z in troubleLayers:
					f.write(z + "\n")
				f.close()
			f.close()
	except:
		AddMsgAndPrint(arcpy.GetMessages())
		AddMsgAndPrint("Unexpected error: ", sys.exc_info()[0])
		AddMsgAndPrint(traceback.print_exc())
	
def FolderStart(workspace, Quiet, FixSource, logFile):
	#Function to handle start of script if user inputs a folder/workspace
	walk = os.walk(workspace, topdown=True)
	for dirpath, dirnames, filenames in walk:
		for filename in filenames:
			if filename[-4:] == ".mxd":
				fullpath = os.path.join(dirpath, filename)
				AddMsgAndPrint("Checking: " + fullpath)
				TestMXD(fullpath, Quiet, FixSource, logFile)
				
try:
	##Initial execution of script
	#Check if user input is file or folder and execute as needed
	if os.path.isfile(input):
		if input[-4:] == ".mxd":
			logFile = os.path.join(os.path.dirname(input),(input[input.rfind("\\")+1:-5] + "_MXDLinkReport_" + startTime.strftime("%Y%m%d") + ".txt"))
			AddMsgAndPrint(logFile)
			with open(logFile, 'w') as f:
				f.write("Report for: " + input + "\n\n")
				f.close()
			TestMXD(input, Quiet, FixSource, logFile)
		else:
			AddMsgAndPrint("Selected file is not an MXD")
	elif os.path.isdir(input):
		logFile = os.path.join(input,(os.path.dirname(input)+"_MXDLinkReport_" + startTime.strftime("%Y%m%d") + ".txt"))
		AddMsgAndPrint(logFile)
		with open(logFile, 'w') as f:
			f.write("Report for: " + input + "\n\n")
			f.close()
		FolderStart(input, Quiet, FixSource, logFile)
	else:
		AddMsgAndPrint("Please select an MXD or a folder to search")
	AddMsgAndPrint("File Scan Completed\n" + str(totalFiles) + " files read; " + str(brknNum) + " files broken\n" + "Script execution: " + str(datetime.now()-startTime))

except Exception, e:
	# If an error occurred while running a tool print the messages
	AddMsgAndPrint("Script failure at " + str(datetime.now() - startTime))
	AddMsgAndPrint(arcpy.GetMessages())
	AddMsgAndPrint("Unexpected error: ", sys.exc_info()[0])
	AddMsgAndPrint(traceback.print_exc())