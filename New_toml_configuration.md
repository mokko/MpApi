# unified configuration 
file format for mink and getAttachments using toml format

filename: jobs.toml

```
[SHF] # job label
# Required values for every job: cmd, type, id
cmd = "getPack" # command
# type is usually one of the following: exhibit, group, query, loc
type = "exhibit" # required
id = 469805
label = "gte" # only for getPack
since = 12345 # optional time stamp

[SHF1]
cmd = "chunk"
type = "group"
id = 469805
# chunk doesn't require a label

[STH]
cmd = "getItem"
type = "Object" # N.B.
id = 123456

[SHF3] # example for get_attachments
cmd = "getPack" 
type = "exhibit" 
id = 469805
label = "gte" 
attachments.restriction = "freigegeben" # or "alle" which assets get downloaded (only freigegeben or other)
attachments.name = "Cornelia" # naming policy
```