# Installing MpApi

## Requirements

- Python 3.11 or newer (`tomllib` is in the standard library from 3.11; on older
  Pythons `tomli` is pulled in instead)
- `lxml >= 4.8.0` and `requests >= 2.6` — both installed automatically

## Install from github

```
pip install git+https://github.com/mokko/MpApi
```

## Install from a clone (editable)

```
git clone https://github.com/mokko/MpApi.git
cd MpApi
pip install -e .
```

On a current Linux distribution the system Python is "externally managed" and pip
refuses to install into it. Use a virtual environment in the clone:

```
python3 -m venv .venv
.venv/bin/pip install -e .
```

Both give you the same command line frontends, from the `[project.scripts]` block
in `pyproject.toml`:

```
mink            getAttachments   getAttachment    getItem
getDefinition   updateItem       validate         filter
```

With a virtual environment they live in `.venv/bin/`, so either call them by path
(`.venv/bin/mink`) or activate the environment first:

```
source .venv/bin/activate
```

## Configuration

MpApi expects two files.

**Credentials** at `~/.ria`:

```
user = "EM_XY"
pw = "pass"
baseURL = "https://museumplus-produktiv.spk-berlin.de:8181/MpWeb-mpBerlinStaatlicheMuseen"
```

The instance above is behind a firewall, so it only answers from inside the museum
network.

Note that the credentials are read **at import time**, so every entry point needs
this file — even `mink -h`. Without it you get:

```
SyntaxError: RIA Credentials not found at /home/you/.ria
```

**Jobs** in `jobs.toml`, described in `New_toml_configuration.md`. I keep my jobs
and all the data in a directory `sdata/` inside the MpApi directory (it is not
tracked by git).

## Checking the install

```
mink -h
```

## Notes on packaging

`pyproject.toml` names the module explicitly:

```toml
[tool.flit.module]
name = "mpapi"
```

This is not decoration. Flit looks for a folder matching the project name, and the
project is `MpApi` while the package directory is `src/mpapi`. On a filesystem that
ignores case (Windows, macOS) the two match by accident; on Linux the build fails
with `ValueError: No file/folder found for module MpApi`. Keep the two in step.
