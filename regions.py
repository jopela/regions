#!/usr/bin/python3

import argparse
import logging
import os
import sys

import mtriputils

from iso3166 import countries
from mtriputils import list_guides
from cityinfo import filecityinfo
from cityres import cityres


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
    regions(valid_iso_codes,
            args.guide_path,
            args.target_path,
            args.filename,
            args.endpoint)

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

def regions(countries, guide_path, target_directory, city_filename, endpoint):
    """
    generate regional guides for countries from the city guides found in
    guide_path and save the resulting guide in target_directory.
    """

    # list the leaf guides that can be found under the given path.
    city_guide_files = list_guides(guide_path, city_filename)

    for country in countries:
        # filter the list for the guides that are in this country.
        country_guides_file = [g for g in city_guide_files if guide_in_country(g, country.alpha3, endpoint)]
        print("here are the filename for the following country")
        print("country:{0}".format(country.name),country_guides)

    return None

def guide_in_country(guide_filename, alpha3, endpoint):
    """
    Interrogate the SPARQL endpoint to see if the given guide resides in
    the country specified by the iso3166 alpha3 country code

    EXAMPLE
    =======

    >>> guide_in_country('/root/dev/regions/test/Boston-48/result.json', 'USA', 'http://datastore:8890/sparql')
    True

    >>> guide_in_country('/root/dev/regions/test/Boston-48/result.json', 'CAN', 'http://datastore:8890/sparql')
    False

    """

    # open the guide and find its dbpedia resource.
    search = filecityinfo(guide_filename)
    resource = cityres(search, endpoint)

    # find the country resource of the guide.
    if not resource:
        logging.warning("could not find a dbpedia resource for guide {0}".format(guide_filename))
        return False

    country_resource_1 = guide_country_res(resource, endpoint)

    if not country_resource_1:
        logging.warning("could not find a country reference for {0} associated to guide {1}".format(country_resource_1, guide_filename))
        return False

    # find the country resource of the given alpha3 country code.
    country_resource_2 = alpha3_country_res(alpha3, endpoint)

    if not country_resource_2:
        logging.warning("could not find a country reference for code {0}".format(country_resource_2, alpha3))
        return False

    return country_resource_1 == country_resource_2


def alpha3_country_res(alpha3, endpoint):
    """
    given an iso-3166 alpha3 country code, return the associated country resource.

    EXAMPLE
    =======

    >>> alpha3_country_res('CAN','http://datastore:8890/sparql')
    'http://dbpedia.org/resource/Canada'

    >>> alpha3_country_res('ABW','http://datastore:8890/sparql')
    'http://dbpedia.org/resource/Aruba'

    >>> alpha3_country_res('USA','http://datastore:8890/sparql')
    'http://dbpedia.org/resource/United_States'
    """

    # prepare the query to the sparql endpoint
    query_template = """ select ?uri where {{ ?gadm <http://gadm.geovocab.org/ontology#iso> '{0}' .  ?gadm <http://www.w3.org/2002/07/owl#sameAs> ?uri .  ?uri a dbowl:Country . }} """

    query_instance = query_template.format(alpha3)
    query_result = mtriputils.sparql_query(query_instance, endpoint)

    if len(query_result) > 0:
        return query_result[0][0]
    else:
        return None

def guide_country_res(guide_res, endpoint):
    """
    given a guide dbpedia resource, return it's country resource.

    EXAMPLE
    =======

    >>> guide_country_res('http://dbpedia.org/resource/Montreal','http://datastore:8890/sparql')
    'http://dbpedia.org/resource/Canada'

    """

    # build the query to get the country.
    query_template = """ select ?country where {{ <{0}> dbowl:country ?country .}} """

    query_instance = query_template.format(guide_res)
    # sends the request to the endpoint.
    query_result = mtriputils.sparql_query(query_instance, endpoint)

    # return the first element of the first tuple.
    if len(query_result) > 0:
        return query_result[0][0]
    else:
        return None

def country_code_list():
    """
    generates a list of tuple for every country. Tuples are of the form
    ('country name', 'alpha3 code')
    """

    result = [(c.name,c.alpha3) for c in countries]
    return result

if __name__ == '__main__':
    main()

