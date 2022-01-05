# MpApi - Unofficial API client for Zetcom's MuseumPlus

API Specification: http://docs.zetcom.com/ws

Libraries
* mpapi.py   - low level client; all endpoints; agnostic of metadata format  
* sar.py     - search and response; slightly higher level client; specific to Berlin instance
* chunky.py  - search responses in chunks

Frontends and CLI utils
* mink.py    - command line frontend for MpApi; write your own jobs in jobs.dsl
* getItem.py - just download one moduleItem to your taste
* replace.py - mechanism for mass search/replace tasks (still early in 
			   development)

Scripts (installed in path)
* mink
* MPreplace

Example Plugins for Replace.py
* see replace/*

Requirements
* Python 3.9
* lxml
* requests

For Testing
* pytest 
