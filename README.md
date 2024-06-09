# MpApi - Unofficial API client for Zetcom's MuseumPlus

API Specification: http://docs.zetcom.com/ws

Libraries
* mpapi.py   - low level client; all endpoints; agnostic of metadata format
* search.py  - make a MuseumPlus query
* module.py  - encapsulate data from or for MuseumPlus's modules
* sar.py     - search and response; slightly higher level client; specific to Berlin instance
* chunky.py  - request responses in chunks

Scripts (installed in path, command line)
* mink       - write your own jobs and execute them with cli command
* getAttachments - download attachments from multimedia items (using groups etc.)

For Debugging
* getAttachment - get single attachments
* getItem - get a single item
* getDefinition - ask MuseumPlus for instace's definitions
* updateItem - work in progress
* validate - validate native xml

Requirements
* Python 3.11 (?) - not sure about exact Python version required
* lxml
* requests

For Testing
* pytest 

# Version History
* 0.1.10 20240604
	* unified configuration using jobs.toml
* 0.1.8 20230801 
    * general package cleanup, 
	* changed several vocabulary endpoints to have more consistent names and parameters
    * added Vocabulary class in analogy to Module
* 0.1.7 new credentials
* 0.1.6 20221226
	* chunks are now zipped to save disk space
* 20221210
	* use separate command getAttachments to d/l attachments
* 0.1.5 20220710 adds getAttachments script.

