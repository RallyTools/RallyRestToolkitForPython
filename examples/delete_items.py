#!/usr/bin/env python

#################################################################################################
#
# delete_items.py -- Delete artifacts of the specified type that meet
#                    some expressable criteria
#
USAGE = """
Usage: delete_items.py <entity_name> <criteria>
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

    if len(args) != 2:
        errout(USAGE)
        sys.exit(2)
    entity_name, criteria = args
    if entity_name in STORY_ALIASES:
        entity_name = 'HierarchicalRequirement'

    response = rally.get(entity_name, fetch="ObjectID,FormattedID,Name,CreatedDate,LastUpdateDate", query=criteria,
                         workspace=workspace, project=project,
                         order="ObjectID DESC", limit=200)

    print(f'query resultCount: {response.resultCount}')
    all_items = [item for item in response]
    youngest_item = all_items[0]
    oldest_item   = all_items[-1]
    print(f"youngest item meeting criteria: {youngest_item.FormattedID}")
    print(f"oldest   item meeting criteria: {oldest_item.FormattedID}")
    for ix, item in enumerate(all_items):
        result = rally.delete('UserStory', item.oid)
        assert result == True
        if (ix +1) % 50 == 0:
            print(f'{ix+1} items deleted...')

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
