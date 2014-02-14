#!/usr/bin/python3

import argparse
import logging
import os
import sys

from iso3166 import countries

def main():

    parser = argparse.ArgumentParser()

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

    # country code assignement and validation.
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
    print("my super regional guides",args.countries)
    return

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
    other wise
    Will log the invalid match in the log file.
    """

    is_country = True
    try:
        country = countries[alpha3]
    except KeyError:
        logging.warning('alpha3 code {0} is not a valid'\
                ' country code. It will not be processed. Please invoke the'\
                ' program with the -C flag for the list of valid iso 3166' \
                ' alpha3 country codes '.format(alpha3))
        is_country = False

    return is_country

def regions(countries, guide_path, target_directory):
    """
    generate regional guides for countries from the city guides found in
    guide_path and save the resulting guide in target_directory.
    """

    return None

def country_code_list():
    """
    generates a list of tuple for every country. Tuples are of the form
    ('country name', 'alpha3 code')
    """

    result = [ (c.name,c.alpha3) for c in countries]
    return result

if __name__ == '__main__':
    main()

