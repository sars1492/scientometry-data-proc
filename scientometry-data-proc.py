#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# scientometry-data-proc.py -- A scientometric data processing script.
#
# Copyright (C) 2016  Juraj Szász <juraj.szasz3@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""A scientometric data processing script.

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

"""

from __future__ import unicode_literals
import argparse
import unicodecsv
import yaml
import glob
import os

__version__ = "0.1"


class SectionConfig:

    """Configuration container for a single section.

    SectionConfig object stores configuration for a single section in the format
    that can be directly distributed among all the other objects.

    Attributes:
    year_list -- list of the processed years
    citation_registers -- list of the processed citation registers
    source_data_files -- dict of source data files for each citation register
    process_journals -- boolean defining whether or not to process journals
    journal_catalog_file -- journal catalog file name
    merged_data_file -- merged source file name
    output_directory -- directory name for the output files
    citations_data_file -- name of the citations data file
    publications_data_file -- name of the publications data file
    journals_data_file -- name of the journals data file

    """

    def __init__(self, section_name, section_config):
        """Initialize SectionConfig object.

        Encapsulates section configuration loaded by ConfigFileParser into a
        container object (SectionConfig).  The 'section_name' argument defines
        prefix of the source and output files.  The source data file suffix is
        determined according to 'data' attribute.  When 'date' is set to
        'latest', the most recent source file is selected.

        Positional arguments:
        section_name -- name of the section
        section_config -- configuration dict extracted by ConfigFileParser

        """
        min_year, max_year = section_config['years'].split('-')
        year_list = range(int(min_year), int(max_year)+1)
        self.year_list = [str(x) for x in year_list]

        self.citation_registers = section_config['citation-registers']
        source_data_files = {}
        for cit_reg in self.citation_registers:
            file_prefix = section_name + "-" + cit_reg.lower()
            if section_config['date'] == 'latest':
                file_list = sorted(glob.glob(file_prefix + "*"))
                source_data_files[cit_reg] = file_list[-1] if file_list else file_prefix
            else:
                source_data_files[cit_reg] = file_prefix + "-" + section_config['date']
        self.source_data_files = source_data_files

        self.process_journals = section_config['process-journals']
        self.journal_catalog_file = section_config['journal-catalog-file']

        file_prefix = section_name + "-merged"
        if section_config['date'] == 'latest':
            file_list = sorted(glob.glob(file_prefix + "*"))
            merged_data_file = file_list[-1] if file_list else file_prefix
        else:
            merged_data_file = file_prefix + "-" + section_config['date']
        self.merged_data_file = merged_data_file

        output_directory = section_config['output-dir']
        dir_prefix = output_directory + "/" if output_directory else ""
        self.output_directory= output_directory
        self.citations_data_file = dir_prefix + section_name + "-" + section_config['publications-data-file-suffix']
        self.publications_data_file = dir_prefix + section_name + "-" + section_config['citations-data-file-suffix']
        self.journals_data_file = dir_prefix + section_name + "-" + section_config['journals-data-file-suffix']


class ConfigFileParser:

    """Configuration YAML file parser.

    Parses configuration YAML file and extracts them into a dictionary of
    SectionConfig objects {'section_name': SectionConfig object}, containing
    configuration of all section found in the parsed configuration file
    ('section_config_dict').

    Attributes:
    section_config_dict -- dict containing SectionConfig objects for all sections

    """

    def __init__(self, config_file):
        """Initialize ConfigFileParser object.

        Parses config YAML file ('config_file') and extracts configuration from
        the individual YAML sections.  The 'defaults' YAML section is extracted
        first and its content is then merged into every single section-specific
        configuration.  The resulting dictionary is being used for instantiation
        of the SectionConfig object for each individual section.  These objects
        are stored into the 'section_config_dict' attribute.

        Positional arguments:
        config_file -- configuration YAML file name

        """
        with open(config_file, 'r') as yaml_file:
            yaml_dict = yaml.load(yaml_file)

        section_config_dict = {}
        default_config = yaml_dict['defaults']

        for section, config in yaml_dict.iteritems():
            if section != 'defaults':
                if config:
                    section_config_dict[section] = SectionConfig(section, dict(default_config.items() + config.items()))
                else:
                    section_config_dict[section] = SectionConfig(section, default_config)

        self.section_config_dict = section_config_dict

    def select_sections(self, selected_sections=None):
        """Select subset of SectionConfig objects from 'section_config_dict'.

        Selects subset of SectionConfig objects defined by the
        'selected_sections' argument from the 'section_config_dict' attribute.
        If the argument is undefined, all available SectionConfig objects will
        be selected.

        Keyword arguments:
        selected_sections -- list of plot names (default: None)

        Returns list of SectionConfig objects for the selected sections.

        """
        if selected_sections:
            return [self.section_config_dict[x] for x in selected_sections]
        else:
            return self.section_config_dict.values()


class JournalCatalog:

    """Data container for a journal catalog.

    Parses journal catalog file using unicodecsv.DictReader.  Data are saved
    into a dictionary ('journal_dict').

    Attributes:
    journal_dict -- dictionary of journal catalog data

    """

    def __init__(self, journal_catalog_file):
        """Parse journal catalog file and initialize JournalCatalog object.

        Uses unicodecsv.DictReader to parse given CSV file
        ('journal_catalog_file') and extracts its contents into 'journal_dict'
        attribute.

        Positional arguments:
        journal_catalog_file -- journal catalog file name

        """
        with open(journal_catalog_file) as csv_file:
            csv_dict_reader = unicodecsv.DictReader(csv_file, encoding='utf-8-sig')
            journal_dict = {}
            for row in csv_dict_reader:
                journal_dict[row['Journal']] = [row['IF'], row['SJR']]
        self.journal_dict = journal_dict


class ScientometryData:

    """Data container for a single set of the source scientometric data

    Parses source data file using unicodecsv.DictReader into a list of rows
    ('data').  The class also provides a set of useful methods for further data
    processing.

    Attributes:
    data -- extracted scientometric data

    """

    def __init__(self, data_file):
        """Parse source data file and initialize ScientometryData object.

        Uses unicodecsv.DictReader to parse given CSV file ('data_file') and
        extracts its contents into 'journal_dict' attribute.

        Positional arguments:
        data_file -- source data file name

        """
        with open(data_file, 'r') as csv_file:
            csv_dict_reader = unicodecsv.DictReader(csv_file, encoding='utf-8-sig')
            data = []
            for row in csv_dict_reader:
                data.append(row)
        self.data = data

    def publication_counts_per_year(self, year_list=None):
        """Count number of publications per each year.

        Counts lines containing the same year and maps these counts onto the
        year_list, returning the dictionary of the publication counts per year.
        If the year list is not specified, an intrinsic set of unique years
        extracted from the data is being used instead.

        Keyword arguments:
        year_list -- list of processed years (default: None)

        Returns dictionary of publication counts per year.

        """
        if not year_list:
            year_list = set([row['Year'] for row in self.data])

        publication_count_dict = {k: 0 for k in year_list}
        for row in self.data:
            if row['Year'] in year_list:
                publication_count_dict[row['Year']] += 1

        return publication_count_dict

    def citation_counts_per_year(self, year_list=None):
        """Count number of citations per each year.

        Sums citations on the lines containing the same year and maps these sums
        onto the year_list, returning the dictionary of the citation counts per
        year.  If the year list is not specified, an intrinsic set of unique
        years extracted from the data is being used instead.

        Keyword arguments:
        year_list -- list of processed years (default: None)

        Returns dictionary of citation counts per year.

        """
        if not year_list:
            year_list = set([row['Year'] for row in self.data])

        citation_count_dict = {k: 0 for k in year_list}
        for row in self.data:
            if row['Year'] in year_list:
                citation_count_dict[row['Year']] += int(row['Cites'])

        return citation_count_dict

    def publication_counts_per_journal(self, journal_list=None):
        """Count number of publications per each journal.

        Counts lines containing the same journal and maps these counts onto the
        journal_list, returning the dictionary of the publication counts per
        journal.  If the journal list is not specified, an intrinsic set of
        unique journals extracted from the data is being used instead.

        Keyword arguments:
        journal_list -- list of journals (default: None)

        Returns dictionary of publication counts per jounal.

        """
        if not journal_list:
            journal_list = set([row['Source'] for row in self.data])

        publication_count_dict = {k: 0 for k in journal_list}
        for row in self.data:
            if row['Source'] in journal_list:
                publication_count_dict[row['Source']] += 1

        return publication_count_dict


class PublicationsData:

    """Data container for the publications data.

    Generates and stores publications data based on the dictionary of
    ScientometryData object containing the source scientometric data extracted
    from each individual citation register.  The resulting data can be written
    into a CVS file that can serve as input data file for the
    'scientometry-plot-gen' script.

    Attributes:
    config -- SectionConfig object containing curren section configuration
    fieldnames -- list of field names in the output file header
    data -- list of rows of the publications data

    NOTE: The 'fieldnames' and 'data' attributes are supposed to be used in
    combination with unicodecsv.DictWriter.

    """

    def __init__(self, config, scientometry_data_dict):
        """Initialize PublicationsData object and process given data.

        Processes given 'scientometry_data_dict' in order to get publication
        counts per year per citation register into the table of publication
        counts and and saves it into the 'data' attribute.  Also generates data
        header and saves it into 'fieldnames' attribute.  The 'fieldnames' and
        'data' attributes are supposed to be used in combination with
        unicodecsv.DictWriter.

        Positional arguments:
        config -- SectionConfig object that contains configuration for the
                  current section
        scientometry_data_dict -- dict of ScientometryData objects

        """
        publication_count_dict = {}
        for cit_reg, scientometry_data in scientometry_data_dict.iteritems():
            publication_count_dict[cit_reg] = scientometry_data.publication_counts_per_year(config.year_list)

        fieldnames = ["Year"] + config.citation_registers
        data = []
        for year in config.year_list:
            # Since publication_counts_per_year method returns a dictionary, the
            # publication_count_dict now contains two-dimensional dictionary
            row = [year] + [publication_count_dict[cit_reg][year] for cit_reg in config.citation_registers]
            data.append(dict(zip(fieldnames, row)))

        self.config = config
        self.fieldnames = fieldnames
        self.data = data

    def write_csv_file(self):
        """Write publications data into CSV file

        Uses unicodecsv.DictWriter to write output CSV file with header based on
        the data stored in the 'data' and 'fieldnames' attributes.

        """
        with open(self.config.publications_data_file, 'w') as csv_file:
            csv_dict_writer = unicodecsv.DictWriter(csv_file, fieldnames=self.fieldnames, encoding="utf-8")
            csv_dict_writer.writeheader()
            for row in self.data:
                csv_dict_writer.writerow(row)


class CitationsData:

    """Data container for the citations data.

    Generates and stores citations data based on the dictionary of
    ScientometryData object containing the source scientometric data extracted
    from each individual citation register.  The resulting data can be written
    into a CVS file that can serve as input data file for the
    'scientometry-plot-gen' script.

    Attributes:
    config -- SectionConfig object containing curren section configuration
    fieldnames -- list of field names in the output file header
    data -- list of rows of the publications data

    NOTE: The 'fieldnames' and 'data' attributes are supposed to be used in
    combination with unicodecsv.DictWriter.

    """

    def __init__(self, config, scientometry_data_dict):
        """Initialize CitationsData object and process given data.

        Processes given 'scientometry_data_dict' in order to get citation counts
        per year per citation register into the table of citation counts and
        and saves it into the 'data' attribute.  Also generates data header and
        saves it into 'fieldnames' attribute.

        Positional arguments:
        config -- SectionConfig object that contains configuration for the
                  current section
        scientometry_data_dict -- dict of ScientometryData objects

        """
        citation_count_dict = {}
        for cit_reg, scientometry_data in scientometry_data_dict.iteritems():
            citation_count_dict[cit_reg] = scientometry_data.citation_counts_per_year(config.year_list)

        fieldnames = ["Year"] + config.citation_registers
        data = []
        for year in config.year_list:
            # Since publication_counts_per_year method returns a dictionary, the
            # publication_count_dict now contains two-dimensional dictionary
            row = [year] + [citation_count_dict[cit_reg][year] for cit_reg in config.citation_registers]
            data.append(dict(zip(fieldnames, row)))

        self.config = config
        self.fieldnames = fieldnames
        self.data = data


    def write_csv_file(self):
        """Write citation data into CSV file

        Uses unicodecsv.DictWriter to write output CSV file with header based on
        the data stored in the 'data' and 'fieldnames' attributes.

        """
        with open(self.config.citations_data_file, 'w') as csv_file:
            csv_dict_writer = unicodecsv.DictWriter(csv_file, fieldnames=self.fieldnames)

            csv_dict_writer.writeheader()
            for row in self.data:
                csv_dict_writer.writerow(row)


class JournalsData:

    """Data container for the journals data.

    Generates and stores journals data based on the ScientometryData object,
    containing the merged source scientometric data, and JournalCatalog object,
    containing citation indicators for all journals.  The resulting data can be
    written into a CVS file.

    Attributes:
    config -- SectionConfig object containing curren section configuration
    fieldnames -- list of field names in the output file header
    data -- list of rows of the publications data

    NOTE: The 'fieldnames' and 'data' attributes are supposed to be used in
    combination with unicodecsv.DictWriter.

    """

    def __init__(self, config, scientometry_data, journal_catalog):
        """Initialize JournalsData object and process given data.

        Processes given 'scientometry_data' object in order to get publicaton
        counts per journal into the table of journal counts that is left-joined
        with the dict in the given 'journal_catalog' object.  Saves the
        resulting table into the 'data' attribute.  Also generates data header
        and saves it into 'fieldnames' attribute.

        Positional arguments:
        config -- configuration for the current section
        scientometry_data -- ScientometryData object containing data of the
                             merged data file
        journal_catalog -- JournalCatalog object containing data of the journal
                           catalog

        """
        publication_count_dict = scientometry_data.publication_counts_per_journal()
        journal_list = sorted(publication_count_dict.keys())
        fieldnames = ["Journal", "Publications", "IF", "SJR"]
        data = []
        for journal in journal_list:
            if journal in journal_catalog.journal_dict:
                row = [journal, publication_count_dict[journal]] + journal_catalog.journal_dict[journal]
            else:
                row = [journal, publication_count_dict[journal], None, None]
            data.append(dict(zip(fieldnames, row)))

        self.config = config
        self.fieldnames = fieldnames
        self.data = data

    def write_csv_file(self):
        """Write journals data into CSV file

        Uses unicodecsv.DictWriter to write output CSV file with header based on
        the data stored in the 'data' and 'fieldnames' attributes.

        """
        with open(self.config.journals_data_file, 'w') as csv_file:
            csv_dict_writer = unicodecsv.DictWriter(csv_file, fieldnames=self.fieldnames, encoding='utf-8')
            csv_dict_writer.writeheader()
            for row in self.data:
                csv_dict_writer.writerow(row)


def main():
    """Run initial code when this module is executed as a script.

    1. Parse command line arguments using argparse.ArgumentParser object.
    2. Extract configuration from YAML file into the list of SectionConfig
       objects using ConfigFileParser object.
    3. Iterate over all sections and process data files:
       a. Load all source data files into dict of ScientometryData objects.
       b. Create output directory if it doesn't exist.
       c. Instantiate PublicationsData object and write CSV file.
       d. Instantiate CitationsData object and write CSV file.
       e. If process-journals option is set to 'true', load journal catalog file
          into JournalCatalog object and merged data file into ScientometryData
          object.  Instantiate JournalsData object and write CSV file.

    """
    description = "Process set of scientometric data defined in " + \
                  "CONFIG_FILE ('config.yaml' as default).  If no SECTION " + \
                  "is specified, all sections defined in CONFIG_FILE will " + \
                  "be processed."
    epilog = "Data for each individual section are loaded from the set of " + \
             "files in CSV format, named " + \
             "'<SECTION_NAME>-<CITATION_REGISTER>-<DATE>.csv', all located " + \
             "in the working directory.  Citation register (in lowercase) " + \
             "has to, case-insensitively, match the citation registers " + \
             "defined in CONFIG_FILE.  The data file containing merged " + \
             "data from all citation registers has to use word 'merged' as " + \
             "citation register in its filename.  The date (in " + \
             "YYYY-MM-DD format) provides file versioning information and " + \
             "it can be used for filtering out specific version according " + \
             "to the value of the 'date' option defined in CONFIG_FILE."
    arg_parser = argparse.ArgumentParser(description=description, epilog=epilog)
    arg_parser.add_argument("-c", metavar="CONFIG_FILE", dest='config_file', default="config.yaml",
                            help="load configuration from CONFIG_FILE")
    arg_parser.add_argument("sections", metavar="SECTION", nargs='*',
                            help="section defined in CONFIG_FILE")
    args = arg_parser.parse_args()

    config_file_parser = ConfigFileParser(args.config_file)
    section_config_list = config_file_parser.select_sections(args.sections)

    for section_config in section_config_list:
        scientometry_data_dict = {}
        for cit_reg, source_data_file in section_config.source_data_files.iteritems():
            scientometry_data_dict[cit_reg] = ScientometryData(source_data_file)

        if not os.path.exists(section_config.output_directory):
            print "Creating directory", section_config.output_directory, "..."
            os.makedirs(section_config.output_directory)

        publications_data = PublicationsData(section_config, scientometry_data_dict)
        print "Generating", section_config.publications_data_file, "..."
        publications_data.write_csv_file()

        citations_data = CitationsData(section_config, scientometry_data_dict)
        print "Generating", section_config.citations_data_file, "..."
        citations_data.write_csv_file()

        if section_config.process_journals:
            journal_catalog = JournalCatalog(section_config.journal_catalog_file)
            merged_scientometry_data = ScientometryData(section_config.merged_data_file)
            journals_data = JournalsData(section_config, merged_scientometry_data, journal_catalog)
            print "Generating", section_config.journals_data_file, "..."
            journals_data.write_csv_file()


if __name__ == "__main__":
    # This code is executed only when scientometry-data-proc is being run
    # directly as a script.  Since local variables are allocated much faster
    # than global variables, it is a good practice to encapsulate whole initial
    # code into the main() function.
    main()
