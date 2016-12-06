#!/usr/bin/env python

#################################################################################################
#
# allowedValues.py -- Allowed Values lister, shows the allowed values for the given
#                     entity and attribute name
#
# NOTE: Be aware as of Oct 2016 that the only attributes that have _meaningful_ values
#       are those of type RATING, STATE and some whose type STRING (but not all whose 
#       type is STRING).
#       There are numerous standard AgileCentral entity attributes of type STRING
#       whose allowedValues reference url returns a True value upon hitting the endpoint.
#       As it that is the only value, it's not really useful as compared to the other
#       attributes that do have multiple allowed values.
#
USAGE = """
Usage: py allowedValues.py entity [attribute attribute ...]

       if not specified, all attributes of the target entity that
       have meaningful allowedValues are examined and listed
"""
#################################################################################################

import sys
import re

from pyral import Rally, rallyWorkset

#################################################################################################

errout = sys.stderr.write

CAMEL_CASED_NAME_PATT = re.compile('([a-z])([A-Z][a-z])')

#################################################################################################

def main(args):

    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    entity = args.pop(0)
    attributes  = args
    server, user, password, apikey, workspace, project = rallyWorkset(options)
    print(" ".join(["|%s|" % item for item in [server, user, password, apikey, workspace, project]]))

    #rally = Rally(server, user, password, apikey=apikey, workspace=workspace, project=project, server_ping=False)
    rally = Rally(server, user, password, apikey=apikey,server_ping=False)
    rally.enableLogging('rally.hist.avl')  # name of file you want the logging to go to

    target = entity
    if entity in ['Story', 'User Story', 'UserStory']:
        entity = "HierarchicalRequirement"
        target = entity
    mo = CAMEL_CASED_NAME_PATT.search(entity)
    if mo:
        txfm = re.sub(CAMEL_CASED_NAME_PATT, r'\1 \2', entity)
        print('transforming query target "%s" to "%s"' % (entity, txfm))
        entity = txfm

    print("%s" % entity)

    response = rally.get('TypeDefinition', fetch="Name,Attributes", query='Name = "%s"' % entity)
    # could check for response.errors here...
    if response.errors:
        print("Errors: %s" % response.errors)
    if response.warnings:
        print("Warnings: %s" % response.warnings)
    td = response.next()

    for attribute in td.Attributes:
        attr_name = attribute.Name.replace(' ', '')
        if attributes and attr_name not in attributes:
            continue

        if attribute.AttributeType not in ['STATE', 'RATING', 'STRING']:
            continue

        allowed_values = rally.getAllowedValues(target, attr_name)
        if not allowed_values:
            continue
        print("    %-28.28s    (%s)" % (attr_name, attribute.AttributeType))
        for av in allowed_values:
            print("        |%s|" % av)

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
