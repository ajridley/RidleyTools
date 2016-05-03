##FixLinks.py
##Created Spring 2016 by Adam Ridley, GIS Specialist
#Cottonwood Field Office - Bureau of Land Management
## FixLinks serves as a module to support functions which parse GIS-related file paths and attempt to find matches within the file system.
## FixLinks supports the ReportBrokenMXDs and ReportBrokenLayerFiles scripts

def SortPath(path, Quiet):
	##Function to refine the location of the FindPath search based off of source path contents
	if ("FINAL_DATA" or "Final_Data") in path:
		if path.find("FINAL_DATA") != -1:
			index = path.find("FINAL_DATA")
		elif path.find("Final_Data") != -1:
			index = path.find("Final_Data")
		foundPath = FindPath(path, index, Quiet)
		return foundPath
	elif "SDE_Master_Data" in path:
		foundPath = FindPath(path, path.find("SDE_Master_Data"), Quiet)
		return foundPath
	else:
		foundPath = FindPath(path, path.find("\\",path.find("loc\\")), Quiet)
		return foundPath

def FindPath(sourcePath, startIndex, Quiet):
	##Function to search the DFS for specifc GIS datasets in a structured way and return match results
	import os
	import arcpy
	import difflib
	import ctypes
	from AddMsg import AddMsgAndPrint
	#Test existence of original source path to fix relative paths
	if arcpy.Exists(sourcePath):
		AddMsgAndPrint("original path exists!")
		return sourcePath
	else:
		originalPath = sourcePath #Store the original datasource path for later use
		originalName = originalPath[originalPath.rfind("\\")+1:] #Retrieve the dataset name
		#Test for data pointed to the Q: drive and ask user if it should be repathed locally if Quiet mode is off
		if sourcePath[:2] == "Q:":
			#print "Original pathed to Q drive. Repath locally?"
			if Quiet == False:
				query = str(sourcePath) + "\nData source pathed to Q drive. Repath locally?"
				mbInput = ctypes.windll.user32.MessageBoxA(0, query, "Q repath?",(0x04|0x2000))
				if mbInput == 6:
					sourcePath = sourcePath.replace(sourcePath[:5],"R:",1)
			return "Q: drive"
		#Test if the datasource is a U: drive path, otherwise proceed
		if sourcePath[:2] != ("U:"):
			counter = sourcePath.count("\\",startIndex)
			intLevels = int(3)
			fileFound = int(0)
			exactMatches = []
			closeMatches = []
			searchedDir = []
			result = None
			#The following tests for Final Data or SDE paths were added to focus the search on authoritative data rather than project-based copies that may exist
			if ("FINAL_DATA" or "final_data" or "Final_Data") in sourcePath:
				#This may need code to change the path to accomodate servers with "Final_Data" rather than "FINAL_DATA"
				sourcePath = r"R:\loc\GIS\FINAL_DATA" + sourcePath[sourcePath.find("\\",startIndex+1):]
				AddMsgAndPrint(sourcePath)
			elif ("SDE_MASTER_DATA" or "SDE_Master_Data" or "sde_master_data") in sourcePath:
				sourcePath = r"R:\loc\GIS\SDE_Master_Data" + sourcePath[sourcePath.find("\\",startIndex+1):]
				AddMsgAndPrint(sourcePath)
			try:	
				while counter > intLevels:
					lastCharIndex = sourcePath.rfind("\\")
					sourcePath = sourcePath[:lastCharIndex]
					if arcpy.Exists(sourcePath):
						AddMsgAndPrint("Searching " + sourcePath + " for: " + originalName)
						for dirpath, dirnames, filenames in arcpy.da.Walk(sourcePath):
							##Following three lines are abandoned code to avoid re-searching previously searched directories as the search function backs down the directory.  It was abandoned due to the possibility of not searching a similarly named, but distinct directory in root folders.
							#for dir in searchedDir:
								#if dir in dirnames:
									#dirnames.remove(dir)
							for filename in filenames:
								if filename == originalName:
									#print "Point " + originalPath + " to: " + os.path.join(dirpath,filename)
									exactMatches.append(os.path.join(dirpath,filename))
									fileFound += 1
								if fileFound > 3:
									break
							for matches in difflib.get_close_matches(originalName, filenames, 10, 0.5):
								closeMatches.append(os.path.join(dirpath, matches))
							fileFound += len(closeMatches)
							#searchedDir.append(dirpath[(dirpath.rfind("\\")+1):])
					#else:
						#print "Source path " + sourcePath + " does not exists"
					sourcePath = sourcePath[:(lastCharIndex-1)]
					counter -= 1
					if (len(exactMatches) > 0):
						if  Quiet == False:
							mbInput = ctypes.windll.user32.MessageBoxA(0,str(len(exactMatches)) + " exact matches found.\n Click Yes to review results; Click No to check for close matches", "Continue?",0x04|0x2000)
							if mbInput == 6:
								result = ResultQuery(exactMatches,originalPath)
						else:
							result = exactMatches[0]
					if len(closeMatches) > 0:
						if (Quiet == False) and (counter >=4):
							mbInput = ctypes.windll.user32.MessageBoxA(0,str(len(closeMatches)) + " close matches found.\n Click Yes to review results; Click No to continue search to parent directory", "Continue?",0x04|0x2000)
							if mbInput == 6:
								result = ResultQuery(closeMatches,originalPath)
							if mbInput == 7:
								continue
					if result != None:
						return result
				else:
					result = "No match"
					return result
			except KeyboardInterrupt:
				return "No match"
		else:
			result = "U: drive"
			return result
	
def ResultQuery(matches, originalPath):
	##Function to request MessageBox input from the user
	import ctypes
	for match in matches:
		query = "Repath " + originalPath + " to: \n" + match
		mbInput = ctypes.windll.user32.MessageBoxA(0,str(query),"Is this your card?",0x04|0x2000)
		if mbInput == 6:
			return match
	else:
		return	