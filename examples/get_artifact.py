#!/usr/bin/env python

#################################################################################################
#
# get_artifact.py -- Get info for a specific instance of a Rally type
#                    identified either by a FormattedID value
#
USAGE = """
Usage: get_artifact.py <FormattedID>    
"""
#################################################################################################

import sys
import re
import string

from pyral import Rally, rallyWorkset

#################################################################################################

errout = sys.stderr.write

STORY_ALIASES = ['Story', 'UserStory', 'User Story']

ARTIFACT_TYPE = { 'DE' : 'Defect',
                  'TA' : 'Task',
                  'TC' : 'TestCase',
                  'US' : 'HierarchicalRequirement',
                  'S'  : 'HierarchicalRequirement',
                  'F'  : 'Feature',
                  'I'  : 'Initiative',
                  'T'  : 'Theme',
                }

FORMATTED_ID_PATT = re.compile(r'(?P<prefix>[A-Z]+)\d+')

COMMON_ATTRIBUTES = ['_type', 'oid', '_ref', '_CreatedAt', '_hydrated', 'Name']

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, username, password, apikey, workspace, project = rallyWorkset(options)
    print(f'server: {server}')
    print(f'apikey: {apikey}')
    print(f'workspace: {workspace}')
    print(f'project  : {project}')
    if apikey:
        #rally = Rally(server, apikey=apikey, workspace=workspace, project=project)
        rally = Rally(server, apikey=apikey, workspace=workspace)
    else:
        #rally = Rally(server, user=username, password=password, workspace=workspace, project=project)
        rally = Rally(server, user=username, password=password, workspace=workspace)

    rally.enableLogging('rally.hist.artifact') # name of file you want logging to go to

    if len(args) != 1:
        errout(USAGE)
        sys.exit(2)
    ident = args.pop(0)

    mo = FORMATTED_ID_PATT.match(ident)
    if mo:
        ident_query = 'FormattedID = "%s"' % ident
    else:
        errout('ERROR: Unable to detect a valid Rally FormattedID in your arg: %s\n' % ident)
        sys.exit(3)
    mo = re.match(r'^(?P<art_abbrev>DE|S|US|TA|TC|F|I|T)\d+$', ident)
    if not mo:
        errout('ERROR: Unable to extract a valid Rally artifact type abbrev in %s' % ident)
        sys.exit(4)
    art_abbrev = mo.group('art_abbrev') 
    entity_name = ARTIFACT_TYPE[art_abbrev]

    response = rally.get(entity_name, fetch=True, query=ident_query, workspace=workspace)

    if response.errors:
        errout("Request could not be successfully serviced, error code: %d\n" % response.status_code)
        errout("\n".join(response.errors))
        sys.exit(1)

    if response.resultCount == 0:
        errout('No item found for %s %s\n' % (entity_name, ident))
        sys.exit(4)
    elif response.resultCount > 1:
        errout('WARNING: more than 1 item returned matching your criteria\n')
        sys.exit(5)

    for item in response:
        print(item.details())

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
