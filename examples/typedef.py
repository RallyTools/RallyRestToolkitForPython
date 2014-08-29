#!/usr/bin/env python

#################################################################################################
#
# typedef.py --  obtain the attribute info for a user specified entity along with the full
#                inheritance chain
#
USAGE = """
Usage:  typedef.py <entity_name>
"""
#################################################################################################

import sys
import re

from pyral import Rally, rallyWorkset

#################################################################################################

errout = sys.stderr.write

ATTRIBUTE_FIELDS = \
    """
     ObjectID
     _ref
     _type
     _refObjectName
     _objectVersion
     _CreatedAt
     CreationDate
     Subscription
     Workspace
     ElementName
     Parent
     TypePath
     Name 
     IDPrefix
     AttributeType
     SchemaType
     Required
     ReadOnly
     Custom
     Hidden
     MaxLength
     MaxFractionalDigits
     Constrained
     Filterable
     Owned
     AllowedValueType
     AllowedValues
     AllowedQueryOperators
     Note 
    """.split("\n")

#################################################################################################

def main(args):

    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    if not args:
        print "You must supply an entity name!"
        sys.exit(1)

    query = ""
    target = args[0]
    if target in ['UserStory', 'User Story', 'Story']:
        target = "HierarchicalRequirement"
    if '/' in target:
        parent, entity = target.split('/', 1)
        target = entity
    query = 'ElementName = "%s"' % target

    server, username, password, apikey, workspace, project = rallyWorkset(options)
    try:
        if apikey:
            rally = Rally(server, apikey=apikey, workspace=workspace, project=project)
        else:
            rally = Rally(server, user=username, password=password, workspace=workspace, project=project)
    except Exception as ex:
        errout(str(ex.args[0]))       
        sys.exit(1)

    typedef = rally.typedef(target)
    showAttributes(typedef.Attributes)

    print ""
    print "-" * 64
    print ""
    for ix, ancestor in enumerate(typedef.inheritanceChain()):
        print "%s %s" % (" " * (ix*4), ancestor)

#################################################################################################

def showAttributes(attributes):
    required = []
    optional = []
    av_limit = 20

    for attr in attributes:
        name   = '%s' % attr.ElementName
        a_type = '%s' % attr.AttributeType
        s_type = '%s' % attr.SchemaType
        s_type = s_type.replace('xsd:', '')
        if s_type.upper() == a_type:
            s_type = ''
        reqd   = 'Required' if attr.Required else 'Optional'
        rdonly = 'ReadOnly' if attr.ReadOnly else 'Settable'
        custom = 'Custom'   if attr.Custom   else 'Standard'
        hidden = 'Hidden'   if attr.Hidden   else 'Visible'
        allowedValues = attr.AllowedValues
        tank = required if reqd == 'Required' else optional
        num_allowed_values = ""
        if len(allowedValues) > 0:
           num_allowed_values = ("%d allowed values" % len(allowedValues))
           if len(allowedValues) == 1:
               num_allowed_values = num_allowed_values[:-1]

        info =  "%-32.32s  %-10.10s  %-16.16s  %-10.10s  %-8.8s  %-8.8s  %-7.7s" % \
                (name, a_type, s_type, reqd, rdonly, custom, hidden)
        tank.append(info)
        if num_allowed_values:
            tank.append("  %s" % num_allowed_values)

        for av in allowedValues[:av_limit]:
            av_info = "    |%s|" % av.StringValue
            tank.append(av_info)
        if len(allowedValues) > av_limit:
            tank.append("     ...  %d more values not shown" % (len(allowedValues) - av_limit))

    for item in required + optional:
        print item.encode('utf-8')

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
