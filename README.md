# scientometry-data-proc

A command line script for scientometric data processing that produces set of
data files in CSV format which can be used as an input for further processing
and/or plotting using
[`scientometry-plot-gen`](https://github.com/sars1492/scientometry-plot-gen)
script.  All relevant data processing options are defined by configuration file
in YAML format.  Source data are being loaded from the set of data files in CSV
format located in the same directory.


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
"""A scientometric data processing script.

usage: scientometry-data-proc.py [-h] [-c CONFIG_FILE] [SECTION [SECTION ...]]

Process set of scientometric data defined in CONFIG_FILE ('config.yaml' as
default). If no SECTION is specified, all sections defined in CONFIG_FILE will
be processed.

positional arguments:
  SECTION         section defined in CONFIG_FILE

optional arguments:
  -h, --help      show this help message and exit
  -c CONFIG_FILE  load configuration from CONFIG_FILE

Data for each individual section are loaded from the set of files in CSV format
defined by 'source' key in the CONFIG_FILE. Actual data processing procedure
depends on defined output data class that is defined by 'class' key in the
CONFIG_FILE. The name of the section defines prefix for the output data
files. See project documentation for more details on CONFIG_FILE syntax.
```


## Usage examples

1. Process all sections defined in `config.yaml` (the default configuration
   file):

        $ ./scientometry-data-proc.py

2. Process sections `all-publications-data` and `journals-data` that are defined
   in default config file:

        $ ./scientometry-data-proc.py all-publications-data journals-data

3. You can also load options from the alternative configuration file.  Following
    command processes all sections defined in the `alt-config.yaml`:

        $ ./scientometry-data-proc.py -c alt-config.yaml

4. Making `scientometry-data-proc.py` globally accessible:

        $ cp scientometry-data-proc.py ~/bin
        $ export PATH=$PATH:~/bin
        $ cd ~/data
        $ ls
        data.csv
        alt-config.yaml
        $ scientometry-data-proc.py -c alt-config.yaml


### Configuration file

The configuration file consists of `defaults` section and individual data
processing sections.  Keys and values of all data processing sections are being
merged with the `defaults` section.  If the same key is being specified in both
`defaults` and the data processing section, value defined in the data processing
section overrides the value in the `defaults` section.  Names of the data
processing sections defines the name of the output file or the prefix and/or set
of output files.  Both key and values in the configuration file can contain
UTF-8 characters.


#### List of valid configuration keys

Config. key | Description
------------ | -----------
`output-dir` | Output directory (will be created if it does not exist)
`class` | Output data class (`PublicationsData`, `CitationsData`,`JournalsData`, `ResultsData`, see next section for more details)
`source` | Filename of input file and/or a dictionary of input filenames (keys define dataset labels used in data processing)
`journal-catalog` | Filename of the journal catalog file (used by `JournalsData` class only)
`years` | Range of years for the scientometric analysis (used by `PublicationsData` and `CitationsData` class only)
`groups` | List of dataset groups (used only by `ResultsData` class)
`extract` | List of extracted data columns (used by `ResultsData` class only)
`select` | List of selected columns written to the output file(s).


#### Output data classes

##### PublicationData

Calculates publication count per year for multiple datasets (citation
registers).  The resulting file can be then plotted by *scientometry-plot-gen*.
Output filename is determined by the section name (`{section name}.csv`).
Following table describes valid config keys for this class:

Config. key | Description
------------ | -----------
`source` | Dictionary of filenames--the keys define dataset names used as data column names in the output file
`years` | Range of years defining list of dataset groups that translates into `Group` column of the output file
`select` | List of column names specifying the columns written into the output file (also defines the column order).


##### CitationsData

Calculates total citation count per year of publication for multiple datasets
(citation registers).  The resulting file can be then plotted by
*scientometry-plot-gen*.  Output filename is determined by the section name
(`{section_name}.csv`).  Following table describes valid config keys for this
class:

Config. key | Description
------------ | -----------
`source` | Dictionary of filenames--the keys define dataset names used as data column names in the output file
`years` | Range of years defining list of dataset groups that translates into `Group` column of the output file
`select` | List of column names specifying the columns written into the output file (also defines the column order).


##### JournalsData

Calculates total publication count per journal from the source data that should
contain merged data from all datasets (i.e. citation registers).  The table of
paper counts per journal is then joined with the journal catalog (inner join).
`ISSN` and `Source` columns are removed from the resulting table and the actual
paper counts translate into `Papers` column.  Output filename is determined by
the section name (`{section_name}.csv`).  Following table describes valid config
keys for this class:

Config. key | Description
------------ | -----------
`source` | Filename of the input file
`journal-catalog` | Filename of the journal catalog file (used by `JournalsData` class only)
`select` | List of column names specifying the columns written into the output file (also defines the column order).


##### ResultsData

Extracts data entries from each column the the results data file (exported from
Publish of Perish) and divide them among multiple data files (one per column).
These files have the same form as the output files generated by
`PublicationsData` or `CitationsData` class, although their `Group` column
contain list of dataset group names rather than range of years.  This similarity
is not arbitrary, since these output files are also supposed to be plotted by
*scientometry-plot-gen*.  Dataset group and dataset for each particular data
value is derived from the compound dash-separated string in the `Query` column
(in `{dataset_group}-{dataset}` format).  Output filename is determined by the
combination of the section name and the name of the extracted column
(`{section_name}-{column_name}.csv`--the `{column_name}` suffix is set
to lowercase and spaces are replaced with dashes).  Following table describes
valid config keys for this class:

Config. key | Description
------------ | -----------
`source` | Filename of the input results data file
`groups` | List of dataset groups names translates into `Group` column of the output files (also defines the row order)
`extract` | List of extracted columns (None = all columns will be extracted)
`journal-catalog` | Filename of the journal catalog file (used by `JournalsData` class only)
`select` | List of column names specifying the columns written into the output files (also defines the column order).


#### Example configuration file

```yaml
defaults:
  output-dir: out

publications-data:
  class: PublicationsData
  source:
    Scopus: all-scopus-{date}.csv
    WoS: all-wos-{date}.csv
  years: 2000-2016
  select: [ Year, Scopus, WoS ]

citations-data:
  class: CitationsData
  source:
    Scopus: all-scopus-{date}.csv
    WoS: all-wos-{date}.csv
  years: 2000-2016
  select: [ Year, Scopus, WoS ]

journals-data:
  class: JournalsData
  source: all-merged-{date}.csv
  journal-catalog: journal-catalog-{date}.csv
  select: [ Source title, Papers, ISI JIF, SJR, Scimago h-index, CiteScore, SNIP, Notes ]

results-data:
  class: ResultsData
  source: results-all-{date}.csv
  extract: [ Papers, Citations, Papers_Author, Cites_Paper ]
  select: [ Group, Scopus, WoS, GS ]
```

See [`config.yaml`](examples/config.yaml).


### Source data file

Source data file has to be in CSV (Comma separated Values) format and the first
line has to contain header.  The mandatory columns depends on the output data
class used by particular data processing section.  The `{date}` metavariable in
the source data filename is a placeholder for an arbitrary string--preferably a
date in YYYY-MM-DD format.  If more files in the local directory match the same
pattern, the last one of them (sorted in alphabetical order) will be selected.


#### Example source data file

```
﻿Cites,Authors,Title,Year,Source,Publisher,ArticleURL,CitesURL,GSRank,QueryDate,Type,DOI,ISSN,CitationURL,Volume,Issue,StartPage,EndPage,ECC
1,"A. Šuňovská, V. Hasíková, M. Horník, M. Pipíška, S. Hostin, J. Lesný","Removal of Cd by dried biomass of freshwater moss Vesicularia dubyana: batch and column studies",2016,"Desalination and Water Treatment","","https://www.scopus.com/inward/record.uri?eid=2-s2.0-84953836860&doi=10.1080%2f19443994.2015.1026281&partnerID=40&md5=76fad2aa0cc0fa8627e6a78b0eb5d7cc","",1,"2016-12-21","Article","10.1080/19443994.2015.1026281","","",57,6,2657,2668,1
0,"R. Stasiak-Betlejewska, W. Tomasz, D. Domljan, J. Hollý, P. Vaško","Consumer behavioural research in furniture industry branding-case study of polish enterprise",2016,"27th International Conference on Wood Science and Technology, ICWST 2016: Implementation of Wood Science in Woodworking Sector - Proceedings","","https://www.scopus.com/inward/record.uri?eid=2-s2.0-85003533268&partnerID=40&md5=678f97156b578f6b18cfea0a1491b146","",2,"2016-12-21","Conference Paper","","","",0,0,215,221,0
1,"M. Plesko, J. Suvada, M. Makohusova, I. Waczulikova, D. Behulova, A. Vasilenkova, M. Vargova, A. Stecova, E. Kaiserova, A. Kolenova","The role of CRP,PCT,IL-6 and presepsin in early diagnosis of bacterial infectious complications in paediatric haemato-oncological patients",2016,"Neoplasma","","https://www.scopus.com/inward/record.uri?eid=2-s2.0-84992418592&doi=10.4149%2fneo_2016_512&partnerID=40&md5=427149c58300b5c7fff699a35cefcc9a","",3,"2016-12-21","Article","10.4149/neo_2016_512","","",63,5,752,760,1
5,"V. Frišták, M. Pipíška, J. Lesný, G. Soja, W. Friesl-Hanl, A. Packová","Utilization of biochar sorbents for Cd2+, Zn2+, and Cu2+ ions separation from aqueous solutions: comparative study",2015,"Environmental Monitoring and Assessment","","https://www.scopus.com/inward/record.uri?eid=2-s2.0-84939145701&doi=10.1007%2fs10661-014-4093-y&partnerID=40&md5=bda384bf866e708258f257969052af2a","",4,"2016-12-21","Article","10.1007/s10661-014-4093-y","","",187,1,0,0,5
1,"K. Matelková, R. Boča, ̗. Dlháň, R. Herchel, J. Moncol, I. Svoboda, A. Mašlejová","Dinuclear and polymeric (μ-formato)nickel(II) complexes: Synthesis, structure, spectral and magnetic properties",2015,"Polyhedron","","https://www.scopus.com/inward/record.uri?eid=2-s2.0-84928578956&doi=10.1016%2fj.poly.2015.04.010&partnerID=40&md5=81d5292a5b690ce0b6515cf1ed1ed4c2","",5,"2016-12-21","Article","10.1016/j.poly.2015.04.010","","",95,0,45,53,1
11,"I. Nemec, R. Herchel, I. Svoboda, R. Boča, Z. Trávníček","Large and negative magnetic anisotropy in pentacoordinate mononuclear Ni(II) Schiff base complexes",2015,"Dalton Transactions","","https://www.scopus.com/inward/record.uri?eid=2-s2.0-84930619009&doi=10.1039%2fc5dt00600g&partnerID=40&md5=d862320849df4d7b68d61d04d9238780","",6,"2016-12-21","Article","10.1039/c5dt00600g","","",44,20,9551,9560,11
0,"J. Stubna, M. Hostovecky, D. Tothova","Documentary movies as a motivation in science subjects",2015,"ICETA 2014 - 12th IEEE International Conference on Emerging eLearning Technologies and Applications, Proceedings","","https://www.scopus.com/inward/record.uri?eid=2-s2.0-84990227075&doi=10.1109%2fICETA.2014.7107579&partnerID=40&md5=4c702733b379917e8f059693a342906c","",7,"2016-12-21","Conference Paper","10.1109/ICETA.2014.7107579","","",0,0,169,174,0
2,"J. Horilova, B. Cunderlikova, A.M. Chorvatova","Time- And spectrally resolved characteristics of flavin fluorescence in U87MG cancer cells in culture",2015,"Journal of Biomedical Optics","","https://www.scopus.com/inward/record.uri?eid=2-s2.0-84920518021&doi=10.1117%2f1.JBO.20.5.051017&partnerID=40&md5=bfe93672827dc6cee0e1c7289821fa88","",8,"2016-12-21","Article","10.1117/1.JBO.20.5.051017","","",20,5,0,0,2
12,"S. Hazra, A. Karmakar, M.D.F.C. Guedes Da Silva, L. Dlháň, R. Boča, A.J.L. Pombeiro","Sulfonated Schiff base dinuclear and polymeric copper(ii) complexes: Crystal structures, magnetic properties and catalytic application in Henry reaction",2015,"New Journal of Chemistry","","https://www.scopus.com/inward/record.uri?eid=2-s2.0-84929001179&doi=10.1039%2fc5nj00330j&partnerID=40&md5=cf94269c8147354938b0f92f28082e0b","",9,"2016-12-21","Article","10.1039/c5nj00330j","","",39,5,3424,3434,12
...
```

See [`all-scopus-citations-2016-12-21.csv`](examples/all-scopus-citations-2016-12-21.csv).


### Journal catalog file

Journal catalog file has to be in CSV (Comma separated Values) format and the
first line has to contain header.  The file contains list of journals with
scientometric indicators (if known).  The `{date}` metavariable in the journal
catalog filename is a placeholder for an arbitrary string--preferably a date in
YYYY-MM-DD format.  If more files in the local directory match the same pattern,
the last one of them (sorted in alphabetical order) will be selected.


#### Example journal catalog file

```
Abstract and Applied Analysis,Abstr. Appl. Anal.,1085-3375,1.442,0.512,32,,0.62,0.441
Acta Agronomica Hungarica,Acta Agron. Hung.,0238-0161,0.19,0.134,16,ResearchGate,,
Acta Biologica Cracoviensia Series Botanica,,0001-5296,0.625,0.268,19,,0.63,0.438
Acta Chimica Slovenica,Acta Chim. Slov.,1318-0207,1.167,0.288,35,,0.99,0.528
Acta Crystallographica Section C: Crystal Structure Communications,Acta Crystallogr Sect C Cryst Struct Commun,0108-27
01,0.13,0.24,43,,,
Acta Crystallographica Section C: Structural Chemistry,"Acta crystallogr., C Struct. Chem.",2053-2296,0.479,0.244,6,,0
.57,0.268
Acta Crystallographica Section E: Structure Reports Online,Acta Crystallogr. Sect. E Struct. Rep. Online,1600-5368,0.2
1,0.179,31,,0.17,0.106
Acta Facultatis Pharmaceuticae Universitatis Comenianae,Acta Facultatis Pharmaceuticae Univ. Comenianae,3012298,0.21,0
.195,2,,0.25,0.202
Acta Geologica Slovaca,,1338-5674,0.19,0.169,2,ResearchGate,0.24,0.109
...
```

See [`journal-catalog.csv`](examples/journal-catalog-2016-12-03.csv).


### Resuls data file

Results data file has to be in CSV (Comma separated Values) format and the first
line has to contain header.  The file contains list of data exported from
*Publish or Perish*.  The `{date}` metavariable in the results data filename is
a placeholder for an arbitrary string--preferably a date in YYYY-MM-DD format.
If more files in the local directory match the same pattern, the last one of
them (sorted in alphabetical order) will be selected.

```
Query,Papers,Citations,Papers_Author,Cites_Paper,h_index,g_index,hc_index,hI_index,hI_norm,AWCR,AW_index,AWCRpA,e_index,hm_index
KB-Scopus,380,5234,3.415,5.88,6,11.5,6,1.48,3.5,22.055,4.685,6.37,9.825,2.34
KB-GS,594,7289,8.915,6.5,6.5,11,4.5,1.1,2.5,20.205,4.46,3.805,7.49,1.745
KB-WoS,392,4982,7.2,6.17,7,10.5,5,1.46,3,21.645,4.65,4.755,7.745,2.875
KBt-Scopus,356,11492,4.44,7.76,5,12,5,0.84,3,24.57,4.96,4.9,9.27,1.9
KBt-GS,828,14901,12.1,4.27,7,16,6,1.73,4,37.05,6.09,10.4,12.45,3.33
KBt-WoS,351,3707,5.2,5.7,4,10,4,0.82,3,19.41,4.41,3.43,9,1.98
KCh-Scopus,1106,19248,5.335,10.965,7.5,14.5,6,1.545,4,40.94,6.365,10.98,10.815,3.17
KCh-GS,1525,25208,8.27,10.345,9,16.5,8,2.08,5,53.785,7.285,16.09,13.25,3.59
KCh-WoS,1120,19223,5.76,11.81,7.5,15,6.5,1.525,4,44.275,6.605,11.15,11.855,3.06
...
```

See [`results-all-2017-01-05g.csv`](examples/results-all-2017-01-05.csv).


## License

scientometry-data-proc.py -- A scientometric data processing script.

Copyright (C) 2016, 2017  Juraj Szasz (<juraj.szasz3@gmail.com>)

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hopet hat it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.
﻿
