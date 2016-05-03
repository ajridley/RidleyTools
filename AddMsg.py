##AddMsy.py
##Created Spring 2016 by Adam Ridley, GIS Specialist
#Cottonwood Field Office - Bureau of Land Management
##AddMsg is a module intended to provide dual messaging with print and arcpy.AddMessage, which allows scripts to be run from IDLE, command line, or a ArcGIS Script Tool.

def AddMsgAndPrint(msg, severity=0):
	import arcpy
	# Adds a Message (in case this is run as a tool)
	# and also prints the message to the screen (standard output) 
	
	print msg

	# Split the message on \n first, so that if it's multiple lines, 
	#  a GPMessage will be added for each line
	try:
		for string in msg.split('\n'):
			# Add appropriate geoprocessing message 
			#
			if severity == 0:
				arcpy.AddMessage(string)
			elif severity == 1:
				arcpy.AddWarning(string)
			elif severity == 2:
				arcpy.AddError(string)
	except:
		pass