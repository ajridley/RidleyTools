##ReportBrokenLayerFiles.py
##Created Spring 2016 by Adam Ridley, GIS Specialist
##Cottonwood Field Office - Bureau of Land Management
##This script provides functionality which tests, reports and attempts 
##to locate data sources for broken layer files within the Field Office
##server's Final Data repository.
##This script relies on the FixLinks and AddMsg modules to function properly.

import os
import sys
import arcpy
from datetime import datetime
from FixLinks import SortPath, FindPath
from AddMsg import AddMsgAndPrint

##Set variables
workspace = "R:\loc\GIS\FINAL_DATA"  #Final Data location
#Counters 
brknNum = int(0)
totalFiles = int(0)
startTime = datetime.now() 
#Lists for outputs
brknLayers = []
noSourceLayers = []
troubleLayers = []
fixLayers = []
fixedLayers = []
noMatchLayers = []
#User input for fixing broken links
boolFix = sys.argv[1]

try:
	#Perform walk and iterate through results
	walk = arcpy.da.Walk(workspace, datatype="Layer")
	for dirpath, dirnames, filenames in walk:
		for filename in filenames:
			fullpath = os.path.join(dirpath, filename)
			lyr = arcpy.mapping.Layer(fullpath)
			#Test for broken links and iterate through broken items in layerfile
			brknList = arcpy.mapping.ListBrokenDataSources(lyr)
			for brknItem in brknList:
				AddMsgAndPrint("BROKEN: " + brknItem.name + " at " + brknItem.dataSource)
				#Parse broken data source with FixLinks.SortPath
				foundPath = SortPath(brknItem.dataSource, Quiet = True)
				#Test SortPath results and append to appropriate list
				if foundPath == "No match":
					noMatchLayers.append(fullpath)
				elif foundPath == "U: drive" or foundPath == "Q: drive":
					troubleLayers.append(fullpath)
				elif foundPath != None:
					fixLayers.append(fullpath)
					#Test for fix input from user
					if boolFix == True:
						#Replace datasource and add to fixedLayers if successful
						lyr.replaceDataSource(foundPath, "NONE",'#',validate = True)
						if len(arcpy.GetMessages(2)) == 0:
							fixedLayers.append(fullpath)
				brknNum += 1
			totalFiles += 1
	##Output results
	#Print messages to console and GP dialog
	AddMsgAndPrint(str(len(fixLayers)) + " fixable layers")
	AddMsgAndPrint(str(len(noMatchLayers)) + " unmatchable layers")
	AddMsgAndPrint(str(len(troubleLayers)) + " trouble layers")
	AddMsgAndPrint("File Scan Completed\n" + str(totalFiles) + " files read; " + str(brknNum) + " files broken\n" + "Script execution: " + str(datetime.now()-startTime))
	#Setup and create log file
	logFile = os.path.join(workspace, ("LayerfileReport" + startTime.strftime("%Y%m%d") + ".txt"))
	with open(logFile, 'w') as f:
		f.write(str(len(fixLayers)) + " fixable layers:\n\n")
		for x in fixLayers:
			f.write(x + "\n")
		f.write("\n")
		f.write(str(len(noMatchLayers)) + " broken, but unmatched layers:\n\n")
		for y in noMatchLayers:
			f.write(y + "\n")
		f.write("\n")
		f.write(str(len(troubleLayers)) + " trouble layers:\n\n")
		for z in troubleLayers:
			f.write(z + "\n")
		f.close()
	AddMsgAndPrint("Results available at: " + logFile)
	
except Exception, e:
	import traceback
	# If an error occurred while running a tool print the messages
	AddMsgAndPrint(("Script failure at " + str(datetime.now() - startTime)),severity=0)
	AddMsgAndPrint(arcpy.GetMessages())
	AddMsgAndPrint("Unexpected error: ", sys.exc_info()[0])
	AddMsgAndPrint(traceback.print_exc())
	
