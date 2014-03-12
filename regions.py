#!/usr/bin/python3

import argparse
import logging
import os
import sys

from collections import defaultdict

import mtriputils

from iso3166 import countries
from mtriputils import list_guides
from cityinfo import filecityinfo
from cityres import cityres, filecityres

from filecache import filecache

ADMIN_LEVEL_COUNTRY = 2

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

    sparql_endpoint_default = 'http://datastore:8890/sparql'
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

    hostname_default='162.243.24.168'
    parser.add_argument(
            '-H',
            '--hostname-db',
            help='the hostname of the database containing the FOI schema.'\
                    ' will default to {0} if not specified'.format(
                        hotname_default)
            )

    username_db_default='devmain',
    parser.add_argument(
            '-u',
            '--username-db',
            help='username used to access the database containing the FOI'\
                    'schema. Will default to {0}'.format(username_db_default),
            default=username_db_default

    password_db_default='1guenBIHAJ',
    parser.add_argument(
            '-p',
            '--password-db',
            help='password used to access the database containing the FOI'\
                    'schema. Will default to {0} if not specified'.format(
                        password_db_default),
            default=username_db_default
            )

    database_default = 'gis',
    parser.add_argument(
            '-D',
            '--database-name',
            help='the name of the database containing the FOI schema.'\
                    ' Will default to {0} if not specified'.format(
                        database_default),
            default=database_default
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

    parser.add_argument(
            '-r',
            '--resources',
            help = 'dump the resources for all the iso-3166 country.',
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
            print(c[1],":",c[0])
        logging.info('exit success')
        exit(0)

    if args.resources:
        for c in country_code_list():
            res = alpha3_country_res(c[1], args.endpoint)
            print(c[1],":",c[0],":",res)
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
    regional_guides = regions(valid_iso_codes,
            args.guide_path,
            args.filename,
            args.endpoint,
            args.hostname_db,
            args.username_db,
            args.password_db,
            args.database_name)

    serialize_guides(regional_guides, args.target_path)

    logging.info('regional guide generation terminated')

    return

def serialize_guides(regional_guides, target_path):
    """
    Serialize the guide data structures to disk, saving the result to
    target_path.
    """

    return None

def config_logger(filename, debug):
    """
    Configures the logging library according to our needs.
    """

    logging_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        format='%(asctime)s %(module)s %(levelname)s %(message)s',
        level=logging_level,
        filename=filename)

    return

def valid_country(alpha3):
    """
    Returns True if the given alpha3 code match an existing country. False
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

def regions(countries, guide_path, city_filename, endpoint, hostname,
        username, password, database):
    """
    return regional guides for countries from the city guides found in
    guide_path. The city_filename is the name of the result file
    (usually result.json) and endpoint is a url to the SPARQL endpoint.
    """

    countries_set = set(countries)
    generated_countries_set = set()

    # Compute the dbpedia resource for each guide.
    guide_filenames = list_guides(guide_path, city_filename)

    if len(guide_filenames) < 1:
        logging.error("could not find any guide files located under {0}".format(guide_path))
        exit(-1)

    guides_resources_city = [ (guide_filename, resource_city_guide(guide_filename, endpoint)) for guide_filename in guide_filenames ]

    guides_resources_city_filtered = []
    # report as error all the guide that have no dbpedia resource.
    for grc in guides_resources_city:
        if not grc[1]:
            logging.error("Could not find a city resource for {0}. This guide will not be included in any regional guides".format(grc[0]))
        else:
            guides_resources_city_filtered.append(grc)

    # Compute the country resource of the guides.
    guides_country_resource = [ (t[0], country_resource_city_resource(t[1], endpoint)) for t in guides_resources_city_filtered ]

    guides_country_resource_filtered = []
    # report as error all the guides that have no dbpedia country resource.
    for gcr in guides_country_resource:
        if not  gcr[1]:
            logging.error("Could not find a Country for guide filename {0} (dbres:{1}). This guide will not be included in any regional guides.".format(gcr[0], filecityres(gcr[0],endpoint)))
        else:
            guides_country_resource_filtered.append(gcr)

    # Regroup the guide name by country.
    res = regroup(guides_country_resource_filtered)

    # Build the guides from the formed group if it is part of a country we want to generate.
    guides = []
    for country_resource, guide_filenames in res.items():
        country_alpha3 = iso3166_resource_country_resource(country_resource, endpoint)
        if not country_alpha3:
            logging.error("Could not figure out the ISO3166 alpha3 country codes for the following country resource {0}. If this resource has".format(country_resource))

        elif country_alpha3 in countries_set:
            logging.info("building regional guide for {0}".format(country_alpha3))
            region_guide = build_guide(country_resource, guide_filenames, endpoint, hostname, username, password, database)
            guides.append(region_guide)
            generated_countries_set.add(country_alpha3)
        else:
            logging.info("resource {0} is not required for the current batch guide generation".format(country_resource))
            pass

    diff = countries_set.difference(generated_countries_set)
    if len(diff) > 0:
        logging.error("could not generate a guide for the following region(s):{0}".format(diff))

    return guides

def regroup(tuple_list):
    """
    Bucket the guides into their corresponding country resource.

    EXAMPLE
    =======
    >>> regroup([('/root/dev/regions/test/Montreal-269/result.json','http://dbpedia.org/resource/Canada'), ('/root/dev/regions/test/Quebec-269/result.json','http://dbpedia.org/resource/Canada'), ('/root/dev/regions/test/Paris-69/result.json','http://dbpedia.org/resource/France')])
    defaultdict(<class 'list'>, {'http://dbpedia.org/resource/Canada': ['/root/dev/regions/test/Montreal-269/result.json', '/root/dev/regions/test/Quebec-269/result.json'], 'http://dbpedia.org/resource/France': ['/root/dev/regions/test/Paris-69/result.json']})
    """
    result = defaultdict(list)

    for t in tuple_list:
        result[t[1]].append(t[0])

    return result

def build_guide(country_resource, guide_filenames, endpoint):
    """
    Construct a guide structure from the country_resource.
    """

    # Figure out a name for the guide.
    guide_iso = iso3166_resource_country_resource(country_resource, endpoint)
    guide_name = countries[guide_iso].name
    admin_level = ADMIN_LEVEL_COUNTRY

    # gather the FOIs for the country. (changed for an RPC on a server later on?)
    fois = country_foi(guide_iso, hostname, user, password, db)

    children = []

    return None

def country_foi(guide_iso, hostname, user, password, db):
    """
    Gathers the POI for a country based on.
    """

    fois = []

    # Return all the FOI that are related to a given country.
    return fois

@filecache(None)
def iso3166_resource_country_resource(resource, endpoint):
    """
    From the dbpedia resource of a city, return the iso3166 code of it.

    EXAMPLE
    =======

    >>> iso3166_resource_country_resource('http://dbpedia.org/resource/Canada','http://datastore:8890/sparql')
    'CAN'

    >>> iso3166_resource_country_resource('http://dbpedia.org/resource/France','http://datastore:8890/sparql')
    'FRA'

    >>> iso3166_resource_country_resource('http://dbpedia.org/resource/Russia','http://datastore:8890/sparql')
    'RUS'
    """

    query_template = """
    select ?iso where
    {{
        ?gadm <http://gadm.geovocab.org/ontology#iso> ?iso .
        ?gadm <http://www.w3.org/2002/07/owl#sameAs> <{0}> .
    }}
    """

    query_instance = query_template.format(resource)
    query_result = mtriputils.sparql_query(query_instance, endpoint)

    res = first_result(query_result)

    return res

def country_resource_city_resource(resource, endpoint):
    """
    Return the country resource of a given city.

    EXAMPLE
    =======

    >>> country_resource_city_resource('http://dbpedia.org/resource/Montreal','http://datastore:8890/sparql')
    'http://dbpedia.org/resource/Canada'

    >>> country_resource_city_resource('http://dbpedia.org/resource/Moscow','http://datastore:8890/sparql')
    'http://dbpedia.org/resource/Russia'

    >>> country_resource_city_resource('http://dbpedia.org/resource/Paris','http://datastore:8890/sparql')
    'http://dbpedia.org/resource/France'

    >>> country_resource_city_resource('http://dbpedia.org/resource/Liverpool', 'http://datastore:8890/sparql')
    'http://dbpedia.org/resource/United_Kingdom'

    """

    query_template = """
    select ?country where {{ <{0}> dbowl:country ?country }}
    """

    query_instance = query_template.format(resource)
    query_result = mtriputils.sparql_query(query_instance, endpoint)

    res = first_result(query_result)
    return res

def first_result(tuple_list):

    if len(tuple_list) > 0 and len(tuple_list[0]) > 0:
        return tuple_list[0][0]
    else:
        return None

def resource_city_guide(guide_filename, endpoint):
    """
    from a guide filename, returns the dbpedia resource uri that represents
    the city of the guide.

    EXAMPLE
    =======

    >>> resource_city_guide('/root/dev/regions/test/London-269/result.json', 'http://datastore:8890/sparql')
    'http://dbpedia.org/resource/London'

    >>> resource_city_guide('/root/dev/regions/test/Boston-48/result.json', 'http://datastore:8890/sparql')
    'http://dbpedia.org/resource/Boston'
    """

    # open the guide up and get the city search string.
    search = filecityinfo(guide_filename)

    # get the dbpedia resource for that city.
    resource = cityres(search, endpoint)

    if not resource:
        return None

    clean = mtriputils.rem_quote(resource)

    return clean

def guide_in_country(guide_filename, alpha3, endpoint):
    """
    Interrogate the SPARQL endpoint to see if the given guide resides in
    the country specified by the iso3166 alpha3 country code.

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

    unquote_resource = mtriputils.rem_quote(resource)
    country_resource_1 = guide_country_res(unquote_resource, endpoint)

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
    Given an iso-3166 alpha3 country code, return the associated country resource.

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
    Given a guide dbpedia resource, return it's country resource.

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
    Generates a list of tuple for every country. Tuples are of the form
    ('country name', 'alpha3 code')
    """

    result = [(c.name,c.alpha3) for c in countries]
    return result

if __name__ == '__main__':
    main()

