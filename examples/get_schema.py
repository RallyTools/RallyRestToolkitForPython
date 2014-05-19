#!/usr/bin/env python

#################################################################################################
#
# get_schema.py --  obtain the schema info for a user specified entity 
#                   returns a SchemaItem instance that when printed results in 
#                   the Entity's attributes formatted in an easy to digest view.
#
USAGE = """
Usage:  get_schema.py <entity_name>
"""

#################################################################################################

import sys
import re

from pyral import Rally, rallySettings

#################################################################################################

errout = sys.stderr.write

SCHEMA_ITEM_ATTRIBUTES = \
    [
     'ref', 
     'ObjectName', 
     'ElementName', 
     'Name', 
     'DisplayName', 
     'TypePath',
     'Abstract',
     'Creatable',
     'Queryable',
     'ReadOnly', 
     'Deletable', 
     'Restorable', 
     'IDPrefix', 
     'Ordinal',
     'Attributes',
    ]

ATTRIBUTE_ATTRIBUTES = \
    [
     'ref', 
     'ObjectName',
     'ElementName', 
     'Name', 
     'AttributeType',
     'Custom',
     'Required',
     'ReadOnly',
     'Filterable',
     'Hidden',
     'SchemaType',
     'Constrained',
     'AllowedValues',
    ]

#################################################################################################

def main(args):

    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, user, password, workspace, project = rallySettings(options)
    #print " ".join(["|%s|" % item for item in [server, user, '********', workspace, project]])

    if not args:
        errout("ERROR: You must supply an entity name!\n")
        sys.exit(1)

    entity = args[0]
    if entity in ['UserStory', 'User Story', 'Story']:
        entity = "HierarchicalRequirement"
    #if '/' in entity:
    #    parent, entity = entity.split('/', 1)

    try:
        rally = Rally(server, user=user, password=password)
    except Exception as ex:
        errout(str(ex.args[0]))       
        sys.exit(1)

    schema_item = rally.typedef(entity)
    print schema_item

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
