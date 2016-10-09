#!/usr/bin/env python

#################################################################################################
#
# getitem.py -- Get info for a specific instance of a Rally type
#               identified either by an OID or a FormattedID value
#
USAGE = """
Usage: getitem.py <entity_name> <OID | FormattedID>    
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
                }

OID_PATT          = re.compile(r'^\d+$')
FORMATTED_ID_PATT = re.compile(r'(?P<prefix>[A-Z]+)\d+')

COMMON_ATTRIBUTES = ['_type', 'oid', '_ref', '_CreatedAt', '_hydrated', 'Name']

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, username, password, apikey, workspace, project = rallyWorkset(options)
    if apikey:
        rally = Rally(server, apikey=apikey, workspace=workspace, project=project)
    else:
        rally = Rally(server, user=username, password=password, workspace=workspace, project=project)

    rally.enableLogging('rally.hist.item') # name of file you want logging to go to

    if len(args) != 2:
        errout(USAGE)
        sys.exit(2)
    entity_name, ident = args
    if entity_name in STORY_ALIASES:
        entity_name = 'HierarchicalRequirement'

    mo = OID_PATT.match(ident)
    if mo:
        ident_query = 'ObjectID = %s' % ident
    else:
        mo = FORMATTED_ID_PATT.match(ident)
        if mo:
            ident_query = 'FormattedID = "%s"' % ident
        else:
            errout('ERROR: Unable to determine ident scheme for %s\n' % ident)
            sys.exit(3)

    response = rally.get(entity_name, fetch=True, query=ident_query, 
                         workspace=workspace, project=project)

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
