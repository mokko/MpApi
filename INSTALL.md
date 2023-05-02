# Installing MpApi

## With `poetry`

```
git clone https://github.com/mokko/MpApi.git
cd MpApi
poetry install
```

## Prerequisites

- python >=3.9
- pip, a package installer that normales comes as part of Python
- lxml
- requests
- tomllib (if python is < 3.11)

## Configuration

Place the configuration and all the data in a directory called `sdata` inside the MpApi directory.

MpApi expects two configuration files:

- `credentials.py`
- `jobs.dsl`: a description of the jobs you plan to run

### `credentials.py`

Contains three lines in pure Python:

```
user = "EM_XY"
pw = "pass"
baseURL = "https://museumplus-produktiv.spk-berlin.de:8181/MpWeb-mpBerlinStaatlicheMuseen" # this instance is behind a firewall
```

### `jobs.dsl`

The job queue might look like this. It is important to keep the indentaion intact!

```
HF-EM-Module: # job label
 	  getPack exhibit 20222 M39
 	  getPack exhibit 21822 Amerika-Ausstellung
 	  getPack exhibit 20215 Südsee-Ausstellung
 	  getPack exhibit 20226 Afrika-Ausstellung
 	  getPack exhibit 20218 Asien-Ausstellung
 	  pack
```

### `getAttachments.ini`

```
[label]
type: group
id: 12345
restriction: None | freigegeben
name: dateiname | mulid
```

Notice that the pipe symbol `|` seperates the possible options.

## Command-Line Interface (CLI): `mink`

Execute `mink` from the directory in which you placed `credentials.py`. This will be your data directory.

Try `mink` to see if everything is installed correctly:

```
mink --help
mink -j HF-EM-Module
```
