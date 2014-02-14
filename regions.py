#!/usr/bin/python3

import argparse
import logging
import os
import sys

from iso3166 import countries
from mtriputils import list_guides

def main():

    parser = argparse.ArgumentParser()

    city_guide_filename_default = 'result.json'
    parser.add_argument(
            '-f',
            '--filename',
            help='the city guides filename. Default to {0} if '\
                    ' not specified'.format(city_guide_filename_default),
            default = city_guide_filename_default
            )

    country_default = countries['Canada'].alpha3
    parser.add_argument(
            '-c',
            '--countries',
            help='The list of iso 3166 alpha3 country code of the regional'\
            ' guides you want to generate. Will default to [{0}] if no'\
                    ' argument is given. The special code ALL will trigger'\
                    ' guide generation for all countries '.format(country_default),
            nargs='+',
            default = [country_default],
            )

    sparql_endpoint_default = 'http://192.168.1.202:8890/sparql'
    parser.add_argument(
            '-e',
            '--endpoint',
            help='The location of the sparql endpoint used for the resource'\
                    ' query. Defaults to {0}'.format(sparql_endpoint_default),
            default = sparql_endpoint_default
            )

    log_file_default = '/var/log/regions.log'
    parser.add_argument(
            '-l',
            '--log-file',
            help='The path to the log file. Defaults to {0}.'.format(
                log_file_default),
            default = log_file_default
            )

    debug_logging_default = False
    parser.add_argument(
            '-d',
            '--debug-messages',
            help='Print the debug message in the log.',
            action='store_true',
            default=debug_logging_default
            )

    parser.add_argument(
            '-C',
            '--country-list',
            help='dumps the iso3166 alpha3 country codes for all countries.'\
                    ' This is helpful when trying to determine the code for'\
                    ' the country you are trying to generate a guide for.',
            action='store_true'
            )

    target_dir_default = './target'
    parser.add_argument(
            '-t',
            '--target-path',
            help='the target directory to which the resulting guides will be'\
                    ' saved. Default to {0} if no'\
                    ' directory is specified.'.format(target_dir_default),
            default = target_dir_default
            )

    guide_path_default = './'
    parser.add_argument(
            '-g',
            '--guide-path',
            help='the folder that contain the city guides.'\
            ' Default to {0} if not specified'.format(guide_path_default),
            default = guide_path_default
            )

    args = parser.parse_args()

    # log config.
    debug = args.debug_messages
    log_file = args.log_file
    config_logger(log_file, debug)

    logging.info('{0} started'.format(sys.argv[0]))

    if args.country_list:
        for c in country_code_list():
            print(c[0],":",c[1])
        logging.info('exit success')
        exit(0)

    # country codes assignement and validation.
    if 'ALL' in args.countries:
        valid_iso_codes = [c.alpha3 for c in countries]
    else:
        valid_iso_codes = [c for c in args.countries if valid_country(c)]

    if len(valid_iso_codes) < 1:
        logging.error('no valid iso3166 alpha3 codes were specified.'\
                ' Regional guide generation aborted.')
        logging.error('exit error code {0}'.format(-1))
        exit(-1)

    logging.info('starting regional guide generation'\
            ' for {0} countries'.format(len(valid_iso_codes)))

    # regional guide generation.
    regions(valid_iso_codes, args.guide_path, args.target_path, args.filename)

    logging.info('regional guide generation terminated')

    return

def serialize_guides(regional_guides, target_path):
    """
    serialize the guide data structures to disk, saving the result to
    target_path.
    """

    return None

def config_logger(filename, debug):
    """
    configures the logging library according to our needs.
    """

    logging_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        format='%(asctime)s %(module)s %(levelname)s %(message)s',
        level=logging_level,
        filename=filename)

    return

def valid_country(alpha3):
    """
    returns True if the given alpha3 code match an existing country. False
    otherwise.  Will log the invalid match in the log file.
    """

    is_country = True
    try:
        country = countries[alpha3]
    except KeyError:
        logging.warning('alpha3 code {0} is not a valid'\
                ' country code. It will not be processed. Please invoke the'\
                ' program with the -C flag for the list of valid iso 3166'\
                ' alpha3 country codes'.format(alpha3))
        is_country = False

    return is_country

def regions(countries, guide_path, target_directory, city_filename):
    """
    generate regional guides for countries from the city guides found in
    guide_path and save the resulting guide in target_directory.
    """

    # list the leaf guides that can be found under the given path.
    city_guide_files = list_guides(guide_path, city_filename)

    for country in countries:
        # filter the list for the guides that are in this country



    return None

def guide_in_country(guide_filename, alpha3, endpoint):
    """
    Interrogate the SPARQL endpoint to see if the given guide resides in
    the country specified by the iso3166 alpha3 country code
    """

    query_template ="""
    select ?uri

    return True

def country_code_list():
    """
    generates a list of tuple for every country. Tuples are of the form
    ('country name', 'alpha3 code')
    """

    result = [ (c.name,c.alpha3) for c in countries]
    return result

if __name__ == '__main__':
    main()

