# MpApi - Unofficial API client for Zetcom's MuseumPlus

API Specification: http://docs.zetcom.com/ws

Libraries

- mpapi.py - low level client; all endpoints; agnostic of metadata format
- sar.py - search and response; slightly higher level client; specific to Berlin instance
- chunky.py - search responses in chunks

Scripts (installed in path, all for the command line)

- mink - write your own jobs and execute them with mink
- MPreplace - replace things in RIA
- getAttachments - download attachments from multimedia items (using groups)

Example Plugins for Replace.py

- see replace/\*

Requirements

- Python 3.9
- lxml
- requests

For Testing

- pytest

## How to Use

For instructions on how to use `mink` and `getAttachments` please take a look at `INSTALL.md`.

## Version History

0.1.5 20220710 adds getAttachments script.
