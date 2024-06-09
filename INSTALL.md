# INSTALLING MpApi
## directly from github
```
pip install git+https://github.com/mokko/MpApi#egg=MpApi
```


## Install from git clone
Or try this for editable install 
```
git clone https://github.com/mokko/MpApi.git
cd MpApi
pip install -e .
```

## Configuration
I put my configuration and all the data in a directory sdata and 
place that inside the MpApi directory.

MpApi expects two configuration files 
- credentials: $home/RIA.toml
- jobs.toml: a description of the jobs you planning to run 

RIA.toml has three lines:
```
user = "EM_XY"
pw = "pass"
baseURL = "https://museumplus-produktiv.spk-berlin.de:8181/MpWeb-mpBerlinStaatlicheMuseen" # this instance is behind a firewall
```

jobs.toml is described in separate file.

## Mink.py as frontend
Use mink as commandline frontend for MpApi. 
Try mink to see if everything is installed correctly:

```
mink -h 
```