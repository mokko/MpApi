# INSTALL MpApi

## Commandline
I am using MpApi from the MS DOS Command console in Windows that you can run with Win + R cmd.

## Prerequisites
* a modern Python 3.x, https://www.python.org/downloads/
* pip, a package installer that normales comes as part of Python
* several Python packages, see below

# Recommended:
* git, e.g. https://git-scm.com/download/win
  I am using the portable version. 

# Required Python Packages
* lxml
* requests
* others?

Install the packages e.g. with 

		> pip install <packagename> 

from commandline.

## INSTALL MpApi with git clone

		> git clone https://github.com/mokko/MpApi.git


## Configuration
I put my configuration and all the data in a directory sdata that 
place inside the MpApi directory.

MpApi expects two configuration files 
- credentials: e.g. in credentials.py
- a description of the jobs you planning to run: jobs.dsl

Credentials.py has three lines in pure Python
		user = "EM_XY"
		pw = "pass"
		baseURL = "https://museumplus-produktiv.spk-berlin.de:8181/MpWeb-mpBerlinStaatlicheMuseen" # this instance is behind a firewall

Here is a section my jobs.dsl
		HF-EM-Module: # job label
			getPackage exhibit 20222 M39                 # 
			getPackage exhibit 21822 Amerika-Ausstellung # 
			getPackage exhibit 20215 Südsee-Ausstellung  # 
			getPackage exhibit 20226 Afrika-Ausstellung	 # 
			getPackage exhibit 20218 Asien-Ausstellung	 # 
			pack 
			

## Mink.py as frontend
Use mink.py as commandline frontend for MpApi.

Try mink to see if everything is installed correctly:
		C:\m3\MpApi\sdata>python ..\src\mink.py
		usage: mink.py [-h] -j JOB [-c CONF]
		mink.py: error: the following arguments are required: -j/--job

