# scientometry-data-proc

A command line script for scientometric data processing that produces set of
data files in CSV format which can be used as an input by
[`scientometry-plot-gen`](https://github.com/sars1492/scientometry-plot-gen) All
relevant data processing options are defined by configuration file in YAML
format.  Source data are being loaded from the set of data files in CSV format
located in the same directory.


## Installation

The `scientometry-data-proc.py` script requires `yaml` and `unicodecsv` Python
packages to run.  The script itself is usually placed into the working
directory, although it could be useful to place it e.g. into `~/bin` directory
and add `~/bin` to `PATH`.  Anyway, in current version, it has to be executed
from the the directory containing data file(s) as there is currently no way to
define alternative path to data files.

Following subsections describe how to install the dependency packages.


### Fedora

    $ sudo dnf install -y python-yaml python-unicodecsv


### CentOS/RHEL

    $ sudo yum install -y python-yaml
    $ sudo pip install unicodecsv


### Ubuntu/Debian

    $ sudo apt-get install python-yaml python-unicodecsv


### Other Linux distro, Apple macOS, Other UNIX-like OS

    $ sudo pip install pyyaml unicodecsv


### MS Windows

    > python -m pip install -U pip setuptools
    > python -m pip install pyyaml unicodecsv


## Synopsis

```
usage: scientometry-data-proc.py [-h] [-c CONFIG_FILE] [SECTION [SECTION ...]]

Process set of scientometric data defined in CONFIG_FILE ('config.yaml' as
default).  If no SECTION is specified, all sections defined in CONFIG_FILE will
be processed.

positional arguments:
  SECTION         section defined in CONFIG_FILE

optional arguments:
  -h, --help      show this help message and exit
  -c CONFIG_FILE  load configuration from CONFIG_FILE

Data for each individual section are loaded from the set of files in CSV format,
named '<SECTION_NAME>-<CITATION_REGISTER>-<DATE>.csv', all located in the
working directory.  Citation register (in lowercase) has to, case-insensitively,
match the citation registers defined in CONFIG_FILE.  The data file containing
merged data from all citation registers has to use word 'merged' as citation
register in its filename.  The date (in YYYY-MM-DD format) provides file
versioning information and it can be used for filtering out specific version
according to the value of the 'date' option defined in CONFIG_FILE.
```


## Usage examples

1. Process all sections defined in `config.yaml` (the default configuration
   file):

        $ ./scientometry-data-proc.py

2. Process sections `all` and `celec` that are defined in default config file:

        $ ./scientometry-data-proc.py all celec

3. You can also load metadata from the alternative configuration file.
    Following command processes all sections defined in the `alt-config.yaml`:

        $ ./scientometry-data-proc.py -c alt-config.yaml

4. Making `scientometry-data-proc.py` globally accessible:

        $ cp scientometry-data-proc.py ~/bin
        $ export PATH=$PATH:~/bin
        $ cd ~/data
        $ ls
        data.csv
        alt-config.yaml
        $ scientometry-plot-gen.py -m alt-config.yaml


### Configuration file

The configuration file consists of `defaults` section and individual data
processing sections.  Keys and values of all data processing sections are being
merged with the `defaults` section.  If the same key is being specified in both
`defaults` and the data processing section, value defined in the data processing
section overrides the value in the `defaults` section.  Names of the data
processing sections has to correspond to the prefix of the source data files.
Values in the configuration file can contain UTF-8 characters.


#### List of valid configuration keys

Configuration keys | Description
------------ | -----------
`years` | Range of years for the scientometric analysis
`date` | Date of the source data file (in `YYYY-MM-DD` format--has to match source data filename suffix; `latest` for the most recent files)
`citation-registers` | List of citation registers (values have to case-insensitively match the middle part of the source data filenames)
`process-journals` | Specify whether to perform the journal processing (`true` or `false`)
`journal-catalog-file` | Filename of the journal catalog file
`output-dir` | Output directory (will be created if it does not exist)
`publications-data-file-suffix` | Filename suffix of the output publications data file
`citations-data-file-suffix` | Filename suffix of the output citations data file
`journals-data-file-suffix` | Filename suffix of the output journals data file


#### Example configuration file

```yaml
defaults:
  years: 2000-2016
  date: latest
  citation-registers:
    - Scopus
    - WoS
    - GS
  process-journals: false
  journal-catalog-file: journal-catalog.csv
  output-dir: out
  publications-data-file-suffix: publications.csv
  citations-data-file-suffix: citations.csv
  journals-data-file-suffix: journals.csv

# All
all:
  process-journals: true

```

See [`config.yaml`](examples/config.yaml).


### Source data file

Source data file has to be in CSV (Comma separated Values) format with at least
three columns where first row contains data header.  Note that only the columns
labeled `Year`, `Cites` and `Source` are relevant for the data processing.  All
the other information contained by the source data file will be ignored.


#### Example source data file

```
Cites,Year,Source
2,2000,Biologia
0,2005,Biologia
0,2000,Neoplasma
3,2001,Nature
17,2002,Biologia
2,2003,Biologia
3,2007,Nature
0,2015,Biologia
1,2004,Neoplasma
0,2014,Neoplasma
1,2006,Nature
3,2006,Biologia
17,2012,Neoplasma
2,2006,Nature
14,2009,Nature
35,2010,Biologia
6,2011,Nature
11,2012,Neoplasma
12,2008,Biologia
12,2012,Neoplasma
0,2013,Nature
```

See [`all-scopus-citations.csv`](examples/all-scopus-citations.csv).


### Journal catalog file

Journal catalog file has to be in CSV (Comma separated Values) format and the
first line has to contain header.  The file contains list of journals with
scientometric indicators (if known).  The `Journal` column contains journal name
that has to match the journal name used in the source data file.  The `IF`
column contains journal *Impact Factor* and `SJR` column contains the *Scimago
Journal and Country Rank* of the journal.


#### Example journal catalog file

```
Journal,IF,SJR
Biologia,1.10,0.322
Nature,38.138,21.936
Neoplasma,1.961,0.726
```

See [`journal-catalog.csv`](examples/journal-catalog.csv).


## License

scientometry-data-proc.py -- A scientometric data processing script.

Copyright (C) 2016  Juraj Szasz (<juraj.szasz3@gmail.com>)

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hopet hat it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.
