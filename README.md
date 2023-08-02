# MpApi - Unofficial API client for Zetcom's MuseumPlus

API Specification: http://docs.zetcom.com/ws

Libraries
* mpapi.py   - low level client; all endpoints; agnostic of metadata format  
* sar.py     - search and response; slightly higher level client; specific to Berlin instance
* chunky.py  - search responses in chunks

Scripts (installed in path, all for the command line)
* mink       - write your own jobs and execute them with mink
* getAttachments - download attachments from multimedia items (using groups)

Example Plugins for Replace.py
* see replace/*

Requirements
* Python 3.9
* lxml
* requests

For Testing
* pytest 

# Version History
0.1.5 20220710 adds getAttachments script.
0.1.7 new credentials
0.1.8 20230801 cleanup, changed several vocabulary endpoints to have more consistent 
	  names and parameters.