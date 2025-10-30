#!/usr/bin/env python

#################################################################################################
#
# get_wksp_schema.py --  obtain the schema info for a workspace specified (or defaulted)
#                        upon instantiation of a pyral Rally instance.
#
USAGE = """
Usage:  get_wksp_schema.py 
"""

#################################################################################################

import sys
import re
from pprint import pprint

from pyral import Rally, rallyWorkset

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

    server, username, password, apikey, workspace, project = rallyWorkset(options)
    try:
        if apikey:
            rally = Rally(server, apikey=apikey, workspace=workspace, project=project)
        else:
            rally = Rally(server, user=username, password=password, workspace=workspace, project=project) 
    except Exception as ex:
        errout(str(ex.args[0]))       
        sys.exit(1)

    schema_blok = rally.getSchemaInfo(workspace)
    print(len(schema_blok))

    nobs = ['Theme', 'HierarchicalRequirement', 'Milestone', 'Objective', 'BusinessObjective', 'KeyResult']
    schema_items = sorted([schema_item for schema_item in schema_blok], key=lambda d: d['Name'])

    for schema_item in schema_items:
        en, name, dn, tp = schema_item['ElementName'], schema_item['Name'], schema_item['DisplayName'], schema_item['TypePath']
        #if en not in nobs:
        #    continue

        #print(f"ElementName: {en}")
        #print(f"DisplayName: {dn}")
        attr_names = [attr['Name'] for attr in schema_item['Attributes']]
        num_attributes = len(attr_names)

        print(f'{en:<32}     Attributes: {num_attributes}')
        """
        if name != dn:
            print(f"       Name: {name}")

        has_parent = schema_item and 'Parent' in schema_item
        if has_parent:
            if schema_item['Parent'] is not None:
                if '_refObjectName' in schema_item['Parent']:
                    parent_name = schema_item['Parent']['_refObjectName']
                    if parent_name != en:
                        print(f"     Parent: {parent_name}")

        if tp != en:
            print(f"   TypePath: {tp}")

        abstract = schema_item['Abstract']
        if abstract:
            print(f"Abstract: {abstract}")

        idpfx = schema_item['IDPrefix']
        if idpfx:
            print(f"IDPrefix: {idpfx}")
        attr_names = [attr['Name'] for attr in schema_item['Attributes']]
        print(f"Attributes: {len(attr_names)}")
        #print(f"   Names: {', '.join(attr_names)}")
        print("-----------")
        """

        # schema_items has 24 keys 
        """
        ['ObjectID', 

         '_ref', 
         '_refObjectName', 
         '_refObjectUUID'

         'Subscription', 
         'Workspace', 

         'ElementName', 
         'Name', 
         'DisplayName', 
         'TypePath', 

         'Abstract', 
         'Parent', 
         'IDPrefix', 

         'Attributes', 

         'Copyable', 
         'Creatable', 
         'ReadOnly', 
         'Queryable', 
         'UserListable', 
         'Deletable', 
         'Restorable', 
         'HierarchyConfigurableType', 
         'Ordinal', 
         'RevisionHistory', 
        ]
        """

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
