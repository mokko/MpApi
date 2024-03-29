# INSTALLING MpApi
## directly from github
> pip install git+https://github.com/mokko/MpApi#egg=MpApi

## new clone
git clone https://github.com/mokko/MpApi.git
> cd MpApi
> pip install
or
> flit install

## from existing git clone
Or try this for editable install 
> cd MpApu
> git pull
> pip install -e .

## Prerequisites
* Python >=3.9, https://www.python.org/downloads/
* pip, a package installer that normales comes as part of Python
* lxml
* requests
* typing_extensions
* some others?

## Configuration
I put my configuration and all the data in a directory sdata and 
place that inside the MpApi directory.

MpApi expects two configuration files 
- credentials: e.g. in credentials.py
- jobs.dsl: a description of the jobs you planning to run 

Credentials.py has three lines in pure Python:
>		user = "EM_XY"
>		pw = "pass"
>		baseURL = "https://museumplus-produktiv.spk-berlin.de:8181/MpWeb-mpBerlinStaatlicheMuseen" # this instance is behind a firewall

Here is a section my jobs.dsl
>	HF-EM-Module: # job label
>		getPack exhibit 20222 M39                  
>		getPack exhibit 21822 Amerika-Ausstellung  
>		getPack exhibit 20215 Südsee-Ausstellung   
>		getPack exhibit 20226 Afrika-Ausstellung   
>		getPack exhibit 20218 Asien-Ausstellung	   
>		pack 

## Mink.py as frontend
Use mink.py as commandline frontend for MpApi. 
Tip: Execute mink from the dir in which you placed credentials.py; this will be your data dir.

Try mink to see if everything is installed correctly:

>	mink -h 	
>	mink -j HF-EM-Module
