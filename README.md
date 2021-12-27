# MpApi - Unofficial API client for Zetcom's MuseumPlus

API Specification: http://docs.zetcom.com/ws

Libraries
* MpApi.py   - low level client 
* Sar.py     - search and response; slightly higher level client

Frontends and CLI utils
* mink.py    - command line frontend for MpApi; write your own jobs in jobs.dsl
* getItem.py - just download one moduleItem to your taste
* Replace.py - mechanism for mass search/replace tasks (still early in development, alpha status)

Example Plugins for Replace.py
* see Replace/*

Requirements
* lxml
* request
* ?