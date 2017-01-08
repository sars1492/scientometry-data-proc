#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
# scientometry-data-proc.py -- A scientometric data processing script.
#
# Copyright (C) 2016, 2017  Juraj Szász <juraj.szasz3@gmail.com>
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

"""

from __future__ import unicode_literals
import argparse
import unicodecsv
import yaml
import glob
import os
from operator import itemgetter

__version__ = "0.4"


class SectionConfig(object):

    """Configuration container for a single section.

    SectionConfig object stores configuration for a single section in the format
    that can be directly distributed among all the other objects.

    Attributes:
    output_data_class -- output data class of the current section
    source_data_file -- source data file  or a dict of source data files
    year_list -- list of the processed years
    group_list -- list of the processed groups
    source_data_files -- dict of source data files for each citation register
    journal_catalog_file -- journal catalog file name
    extract_cols -- list of extracted input columns (for ResultsData class)
    select_cols -- list of selected columns output columns
    output_directory -- directory for output file(s)
    output_data_file -- output data file for the current section

    """

    def __init__(self, section_name, section_config):
        """Initialize SectionConfig object.

        Encapsulates section configuration loaded by ConfigFileParser into a
        container object (SectionConfig).  The 'section_name' argument defines
        prefix of the output file(s).  If output directory is defined by
        'section_config', the directory prefix is automatically prepended to the
        output data filename(s).  Source data files are specified by the
        'source' parameter of the configuration file--it can be either a dict or
        a string.  The filename can contain meta variable patterns that are
        expanded by __eval_filename_pattern() static method.  Note that not all
        attributes are required for particular output data class--these unused
        keys are set to None.

        Positional arguments:
        section_name -- name of the section
        section_config -- configuration dict extracted by ConfigFileParser

        """
        # Initialize 'output_data_class' attribute
        self.output_data_class = section_config['class']

        # Initialize 'source_data_file' attribute
        if type(section_config['source']) is dict:
            source_data_file = {}
            for dataset, filename_pattern in section_config['source'].iteritems():
                filename = self.__eval_filename_pattern(filename_pattern)
                source_data_file[dataset] = filename
        else:
            source_data_file = SectionConfig.__eval_filename_pattern(section_config['source'])
        self.source_data_file = source_data_file

        # Initialize 'year_list' attribute
        if 'years' in section_config:
            min_year, max_year = section_config['years'].split('-')
            year_list = [str(x) for x in range(int(min_year), int(max_year)+1)]
        else:
            year_list = None
        self.year_list = year_list

        # Initialize 'group_list' attribute
        if 'groups' in section_config:
            group_list = section_config['groups']
        else:
            group_list = None
        self.group_list = group_list

        # Initialize 'journal_catalog' attribute
        if 'journal-catalog' in section_config:
            journal_catalog_file = SectionConfig.__eval_filename_pattern(section_config['journal-catalog'])
        else:
            journal_catalog_file = None
        self.journal_catalog_file = journal_catalog_file

        # Initialize 'extract_cols' attribute
        if 'extract' in section_config:
            extract_cols = section_config['extract']
        else:
            extract_cols = None
        self.extract_cols = extract_cols

        # Initialize 'select_cols' attribute
        if 'select' in section_config:
            select_cols = section_config['select']
        else:
            select_cols = None
        self.select_cols = select_cols

        # Initialize 'output_directory' attribute
        if 'output-dir' in section_config:
            output_directory = section_config['output-dir']
        else:
            output_directory = None
        self.output_directory = output_directory

        # Initialize 'output_data_file' attribute
        dir_prefix = (output_directory + "/") if output_directory else ""
        self.output_data_file = dir_prefix + section_name + ".csv"

    @staticmethod
    def __eval_filename_pattern(filename_pattern):
        """Evaluate filename pattern.

        Performs filename pattern expansion.  Currently the only meta variable
        implemented to be used with filename pattern is '{date}' that stands for
        an arbitrary string--preferably a date in YYYY-MM-DD format.  If more
        files in current directory match the pattern, the method returns the
        last one from the list of the matches sorted in alphabetical order.

        Positional arguments:
        filename_pattern -- filename pattern

        Returns the name last file name in current directory that matches the
        pattern.  Returns None if no file matches the pattern.

        """
        if "{date}" in filename_pattern:
            file_list = sorted(glob.glob(filename_pattern.replace("{date}", "*")))
            if file_list:
                return file_list[-1]
            else:
                return None

        return filename_pattern


class ConfigFileParser(object):

    """Configuration YAML file parser.

    Parses configuration YAML file and extracts them into a dictionary of
    SectionConfig objects {'section_name': SectionConfig object}, containing
    configuration of all section found in the parsed configuration file
    ('section_config_dict').

    Attributes:
    section_config_dict -- dict containing SectionConfig objects for all
                           sections

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


class JournalCatalog(object):

    """Data container for a journal catalog.

    Parses journal catalog file using unicodecsv.DictReader.  Data are saved
    into a dictionary ('journal_dict') associated by value from the 'ISSN'
    column.  The 'ISSN' values themselves are deleted from the journal
    dictionary, as well as from the list of field names.

    Attributes:
    fieldnames -- list of the journal catalog data field names
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
        with open(journal_catalog_file, 'r') as csv_file:
            # The 'utf-8-sig' encoding is required, because some input CSV files
            # contain CSV preamble (for UTF-8) that has to be ignored.
            csv_dict_reader = unicodecsv.DictReader(csv_file, encoding='utf-8-sig')
            fieldnames = csv_dict_reader.fieldnames
            fieldnames.remove('ISSN')
            journal_dict = {}
            for row in csv_dict_reader:
                journal_dict[row['ISSN']] = row
                del journal_dict[row['ISSN']]['ISSN']

        self.fieldnames = fieldnames
        self.journal_dict = journal_dict


class ScientometryData(object):

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
            # The 'utf-8-sig' encoding is required, because some input CSV files
            # contain CSV preamble (for UTF-8) that has to be ignored.
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

    def publication_counts_per_journal(self, issn_list=None):
        """Count number of publications per each journal.

        Counts lines containing the same journal ISSN and maps these counts onto
        the issn_list, returning the dictionary of the publication counts per
        journal.  If the journal list is not specified, an intrinsic set of
        unique journals extracted from the data is being used instead.

        Keyword arguments:
        issn_list -- list of journal ISSNs (default: None)

        Returns dictionary of publication counts per jounal.

        """
        if not issn_list:
            issn_list = set([row['ISSN'] for row in self.data if row['ISSN']])

        publication_count_dict = {k: 0 for k in issn_list}
        for row in self.data:
            if row['ISSN'] in issn_list:
                publication_count_dict[row['ISSN']] += 1

        return publication_count_dict

    def extract_results(self):
        """Extract result data.

        The method assumes that the source file contains result data exported
        from Publish and Perish.  It parses string in 'Query' column and
        associates individual data rows into dataset groups and datasets.
        Redundant 'Query' and 'Source' entries are excluded from the extracted
        rows.

        Returns two dimensional dictionary of extracted rows.

        """
        results_dict = {}
        for row in self.data:
            dataset_group, dataset = [x.strip() for x in row['Query'].split("-")[:2]]
            if dataset_group not in results_dict:
                results_dict[dataset_group] = {}
            results_dict[dataset_group][dataset] = row
            del results_dict[dataset_group][dataset]['Query']
            results_dict[dataset_group][dataset].pop("Source", None)

        return results_dict


class OutputData(object):

    """Abstract data container for the output data.

    The abstract class that defines all common attributes and methods for all
    output data classes.  This class shouldn't be used directly.

    Attributes:
    config -- SectionConfig object containing current section configuration
    source_data -- a dict of ScientometryData objects or a sinlge
                   ScientometryData object
    output_file -- name of the output file, a dict of filenames if data are
                   supposed to be written to multiple output files
    fieldnames -- list of field names in the output file header or a dict of
                  such lists
    data -- list of rows of the output data or a dict of such lists

    NOTE: The 'fieldnames' and 'data' attributes are supposed to be used in
    combination with unicodecsv.DictWriter.

    """

    def __init__(self, config):
        """Initialize generic OutputData object.

        Uses config data to instantiate source ScientometryData object(s) and
        initializes all attributes that are common for all output data classes.
        This method has to be explicitly called via super(SubClass, self) at the
        beginning of the __init__ method of the derived subclass.

        Positional arguments:
        config -- SectionConfig object that contains configuration for the
                  current section

        """
        self.config = config

        if type(config.source_data_file) is dict:
            source_data = {}
            for key, data_file in config.source_data_file.iteritems():
                source_data[key] = ScientometryData(data_file)
        else:
            source_data = ScientometryData(config.source_data_file)
        self.source_data = source_data

        self.output_file = config.output_data_file
        self.fieldnames = None
        self.data = None


    def write(self):
        """Write output data into an output file(s).

        Depending on the actual character of the output data this method calls
        OutputData.write_csv() to write either single output file or a set of
        output files.

        """
        if type(self.output_file) is dict:
            for key, data_file in self.output_file.iteritems():
                OutputData.__write_csv(data_file, self.fieldnames[key], self.data[key])
        else:
            OutputData.__write_csv(self.output_file, self.fieldnames, self.data)

    @staticmethod
    def __write_csv(data_file, fieldnames, data, verbose=True):
        """Write data into CSV file

        Uses unicodecsv.DictWriter to write output CSV file with header based on
        the data stored in the 'data' and 'fieldnames' attributes.

        """
        with open(data_file, 'w') as csv_file:
            if verbose:
                print "Generating", data_file, "..."
            # The 'extrasaction' parameter has to be set to 'ignore' because we
            # might want to narrow selection of fields by 'fieldnames'.
            csv_dict_writer = unicodecsv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction='ignore', encoding="utf-8")
            csv_dict_writer.writeheader()
            for row in data:
                csv_dict_writer.writerow(row)


class PublicationsData(OutputData):

    """Data container for the publications data.

    Generates and stores publications data based on the dictionary of
    ScientometryData object containing the source scientometric data extracted
    from each individual citation register.  The resulting data can be written
    into a CSV file that can serve as input data file for the
    'scientometry-plot-gen' script.

    Attributes:
    config -- SectionConfig object containing current section configuration
    source_data -- a dict of ScientometryData objects
    output_file -- name of the output file, a dict of filenames if data are
                   supposed to be written to multiple output files
    fieldnames -- list of field names in the output file header
    data -- list of rows of the output data

    NOTE: The 'fieldnames' and 'data' attributes are supposed to be used in
    combination with unicodecsv.DictWriter.

    """

    def __init__(self, config):
        """Initialize PublicationsData object and process given data.

        Processes given 'scientometry_data_dict' in order to get publication
        counts per year per citation register into the table of publication
        counts and and saves it into the 'data' attribute.  Also generates data
        header and saves it into 'fieldnames' attribute.  The list of field
        names can be are optionally narrowed and/or reordered based on
        'select_cols' attribute of the SectionConfig instance.  The 'fieldnames'
        and 'data' attributes are supposed to be used in combination with
        unicodecsv.DictWriter.

        Positional arguments:
        config -- SectionConfig object that contains configuration for the
                  current section

        """
        super(PublicationsData, self).__init__(config)

        year_list = config.year_list
        dataset_list = config.source_data_file.keys()

        publication_count_dict = {}
        for dataset, source_data in self.source_data.iteritems():
            publication_count_dict[dataset] = source_data.publication_counts_per_year(year_list)

        data = []
        for year in year_list:
            # Since publication_counts_per_year method returns a dictionary, the
            # publication_count_dict now contains two-dimensional dictionary
            row = {k: publication_count_dict[k][year] for k in dataset_list}
            row['Year'] = year
            data.append(row)
        self.data = data

        fieldnames = config.select_cols if config.select_cols else ["Year"] + dataset_list
        self.fieldnames = fieldnames


class CitationsData(OutputData):

    """Data container for the citations data.

    Generates and stores citations data based on the dictionary of
    ScientometryData object containing the source scientometric data extracted
    from each individual citation register.  The resulting data can be written
    into a CSV file that can serve as input data file for the
    'scientometry-plot-gen' script.

    Attributes:
    config -- SectionConfig object containing current section configuration
    source_data -- a dict of ScientometryData objects
    output_file -- name of the output file
    fieldnames -- list of field names in the output file header
    data -- list of rows of the citations data

    NOTE: The 'fieldnames' and 'data' attributes are supposed to be used in
    combination with unicodecsv.DictWriter.

    """

    def __init__(self, config):
        """Initialize CitationsData object and process given data.

        Processes given 'scientometry_data_dict' in order to get citation counts
        per year per citation register into the table of citation counts and and
        saves it into the 'data' attribute.  Also generates data header and
        saves it into 'fieldnames' attribute. The list of field names can be are
        optionally narrowed and/or reordered based on 'select_cols' attribute of
        the SectionConfig instance.

        Positional arguments:
        config -- SectionConfig object that contains configuration for the
                  current section

        """
        super(CitationsData, self).__init__(config)

        year_list = config.year_list
        dataset_list = config.source_data_file.keys()

        citation_count_dict = {}
        for dataset, source_data in self.source_data.iteritems():
            citation_count_dict[dataset] = source_data.citation_counts_per_year(year_list)

        data = []
        for year in config.year_list:
            # Since citation_counts_per_year method returns a dictionary, the
            # publication_count_dict now contains two-dimensional dictionary
            row = {k: citation_count_dict[k][year] for k in dataset_list}
            row['Year'] = year
            data.append(row)
        self.data = data

        fieldnames = config.select_cols if config.select_cols else ["Year"] + dataset_list
        self.fieldnames = fieldnames


class JournalsData(OutputData):

    """Data container for the journals data.

    Generates and stores journals data based on the ScientometryData object,
    containing the merged source scientometric data, and JournalCatalog object,
    containing citation indicators for all journals.  The resulting data can be
    written into a CSV file.

    Attributes:
    config -- SectionConfig object containing current section configuration
    source_data --
                   ScientometryData object
    output_file -- name of the output file, a dict of filenames if data are
                   supposed to be written to multiple output files
    fieldnames -- list of field names in the output file header or a dict of
                  such lists
    data -- list of rows of the output data or a dict of such lists

    NOTE: The 'fieldnames' and 'data' attributes are supposed to be used in
    combination with unicodecsv.DictWriter.

    """

    def __init__(self, config):
        """Initialize JournalsData object and process given data.

        Processes given 'scientometry_data' object in order to get table of
        publicaton counts per journal that is inner-joined with the dict in the
        given 'journal_catalog' object.  Prints warning if ISSN was not found in
        the journal catalog.  Resulting dict is sorted by combination of
        'Papers' column (descending) and 'Source title' column (ascending).  The
        resulting data table and field names are stored into 'data' and
        'fieldnames' attributes respectively.  The list of field names can be
        are optionally narrowed and/or reordered based on 'select_cols'
        attribute of the SectionConfig instance.

        Positional arguments:
        config -- configuration for the current section

        """
        super(JournalsData, self).__init__(config)

        journal_catalog = JournalCatalog(config.journal_catalog_file)
        journal_dict = journal_catalog.journal_dict
        publication_count_dict = self.source_data.publication_counts_per_journal()
        source_issn_list = publication_count_dict.keys()

        data = []
        for issn in source_issn_list:
            if issn in journal_dict.keys():
                row = journal_dict[issn]
                row['Papers'] = publication_count_dict[issn]
                data.append(row)
            else:
                print "WARNING: ISSN", issn, "not found in", config.journal_catalog_file

        if "Source title" in journal_catalog.fieldnames:
            data.sort(key=itemgetter("Source title"))
        data.sort(key=itemgetter("Papers"), reverse=True)
        self.data = data

        fieldnames = config.select_cols if config.select_cols else journal_catalog.fieldnames + ["Papers"]
        self.fieldnames = fieldnames


class ResultsData(OutputData):

    """Data container for the results data.

    Generates and stores results data based on the ScientometryData object,
    containing the exported result data from the Publish or Perish.  Data for
    individual source columns are divided according dataset groups and dataset
    into a dictionary of output data, where each toplevel item contains set of
    output data similar to those generated by PublicationsData and CitationsData
    classes.  The resulting data can be written into a set of CSV files.

    Attributes:
    config -- SectionConfig object containing current section configuration
    source_data -- a dict of ScientometryData objects or a sinlge
                   ScientometryData object
    output_file -- name of the output file, a dict of filenames if data are
                   supposed to be written to multiple output files
    fieldnames -- list of field names in the output file header or a dict of
                  such lists
    data -- list of rows of the output data or a dict of such lists

    NOTE: The 'fieldnames' and 'data' attributes are supposed to be used in
    combination with unicodecsv.DictWriter.

    """

    def __init__(self, config):
        """Initialize ResultsData object and process given data.

        Processes given 'scientometry_data' object in order to extract values
        into set of data tables, using the 'Query' column to determine name of
        dataset group and dataset.  Each individual source data column
        translates into a data matrix [dataset groups x datasets].  Selection of
        the extracted columns can be narrowed using extract_cols attribute or
        the SectionConfig object in the same way as the selection of the output
        columns in all output data matrices can be narrowed/reordered by the
        select_cols attribute.  Each individual output file is composed from the
        section name and the name of the name of extracted column (in lowercase;
        dashes instead of spaces).  The field names, output filenames as well as
        data are stored as a dict, with the name of extracted column as key.

        Positional arguments:
        config -- configuration for the current section

        """
        super(ResultsData, self).__init__(config)

        results_dict = self.source_data.extract_results()

        # Since results_dict is a two-dimensional dictionary, extraction of an
        # arbitrary row requires a single step of two-level nested iteration.
        all_cols = results_dict.itervalues().next().itervalues().next().keys()
        all_groups = sorted(results_dict.keys())

        extract_col_list = config.extract_cols if config.extract_cols else all_cols
        dataset_group_list = config.group_list if config.group_list else all_groups
        dataset_list = results_dict.itervalues().next().keys()
        file_prefix = os.path.splitext(config.output_data_file)[0] + "-"

        output_file_dict = {}
        fieldnames_dict = {}
        data_dict = {}
        for col in extract_col_list:
            output_file_dict[col] = file_prefix + col.replace(" ", "-").lower() + ".csv"
            fieldnames_dict[col] = config.select_cols if config.select_cols else ["Group"] + dataset_list
            data_dict[col] = []
            for dataset_group in dataset_group_list:
                row = {k: x[col] for k, x in results_dict[dataset_group].iteritems()}
                row["Group"] = dataset_group
                data_dict[col].append(row)

        self.output_file = output_file_dict
        self.fieldnames = fieldnames_dict
        self.data = data_dict

def main():
    """Run initial code when this module is executed as a script.

    1. Parse command line arguments using argparse.ArgumentParser object.
    2. Extract configuration from YAML file into the list of SectionConfig
       objects using ConfigFileParser object.
    3. Iterate over all sections and process data files:
       a. Create output directory if it doesn't exist.
       b. Instantiate an object of the class defined by 'output_data_class'
          attribute of the SectionConfig object.
       c. Write output CSV file(s).

    """
    description = "Process set of scientometric data defined in " + \
                  "CONFIG_FILE ('config.yaml' as default).  If no SECTION " + \
                  "is specified, all sections defined in CONFIG_FILE will " + \
                  "be processed."
    epilog = "Data for each individual section are loaded from the set of " + \
             "files in CSV format defined by 'source' key in the " + \
             "CONFIG_FILE.  Actual data processing procedure depends on " + \
             "defined output data class that is defined by 'class' key in " + \
             "the CONFIG_FILE.  The name of the section defines prefix for " + \
             "the output data files.  See project documentation for more " + \
             "details on CONFIG_FILE syntax."
    arg_parser = argparse.ArgumentParser(description=description, epilog=epilog)
    arg_parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    arg_parser.add_argument("-c", metavar="CONFIG_FILE", dest='config_file', default="config.yaml",
                            help="load configuration from CONFIG_FILE")
    arg_parser.add_argument("sections", metavar="SECTION", nargs='*',
                            help="section defined in CONFIG_FILE")
    args = arg_parser.parse_args()

    config_file_parser = ConfigFileParser(args.config_file)
    section_config_list = config_file_parser.select_sections(args.sections)

    for section_config in section_config_list:
        if section_config.output_directory and not os.path.exists(section_config.output_directory):
            print "Creating directory", section_config.output_directory, "..."
            os.makedirs(section_config.output_directory)
        output_data_class = eval(section_config.output_data_class)
        output_data = output_data_class(section_config)
        output_data.write()


if __name__ == "__main__":
    # This code is executed only when scientometry-data-proc is being run
    # directly as a script.  Since local variables are allocated much faster
    # than global variables, it is a good practice to encapsulate whole initial
    # code into the main() function.
    main()
