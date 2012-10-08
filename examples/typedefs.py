#!/opt/local/bin/python2.6

#################################################################################################
#
# typedefs.py --  obtain the attribute info for a user specified entity along with the full
#                 inheritance chain
#
USAGE = """
Usage:  typedefs.py <entity_name>
"""

TODO = """
    Consider pre-loading Project, Release, Iteration, User so we can show human friendly 
    string values along with the ref.
"""
#################################################################################################

import sys
import re

from pyral import Rally, rallySettings

#################################################################################################

# not all, just some of the more interesting TypeDefinition attributes
ATTRIBUTE_FIELDS = "ElementName,TypePath,Parent,Attributes,AttributeType,Abstract,"  +\
                   "Required,Queryable,ReadOnly,Deletable,Hidden,Custom,Filterable," +\
                   "MaxLength,AllowedValues"

errout = sys.stderr.write

TYPEDEF_ATTRS = \
"""
    [
     u'ObjectID', 
     u'_ref', 
     u'_type', 
     u'_refObjectName', 
     u'_objectVersion', 
     u'_CreatedAt', 
     u'CreationDate', 
     u'Subscription', 
     u'Workspace', 
     u'ElementName', 
     u'Parent',
     u'TypePath',
     u'Name', 
     u'AttributeType',
     u'SchemaType', 
     u'Required', 
     u'ReadOnly', 
     u'Custom', 
     u'Hidden', 
     u'MaxLength', 
     u'MaxFractionalDigits', 
     u'Constrained',
     u'Filterable', 
     u'Owned', 
     u'AllowedValueType', 
     u'AllowedValues', 
     u'AllowedQueryOperators',
     u'Note', 
    ]
"""
#################################################################################################

def main(args):

    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, user, password, workspace, project = rallySettings(options)
    #print " ".join(["|%s|" % item for item in [server, user, password, workspace, project]])

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

    try:
        rally = Rally(server, user=user, password=password)
    except Exception as ex:
        errout(str(ex.args[0]))       
        sys.exit(1)
    #rally.enableLogging('rally.hist.typedefs')

    response = rally.get('TypeDefinition', fetch=ATTRIBUTE_FIELDS, query=query, pretty=True,
                                           project=None)
    if response.errors:
        errout("Request could not be successfully serviced, error code: %d\n" % response.status_code)
        errout("\n".join(response.errors))
        sys.exit(1)

    results = response.content[u'QueryResult'][u'Results']
    tdd = results[0]   # tdd <-- type def data

    attrs = tdd[u'Attributes']
    showAttributes(attrs)

    print ""
    print "-" * 64
    print ""
    leaf_td = response.next()
    chain = getHeritage(leaf_td, [])

    for ix, triad in enumerate(chain):
        parent, entity, attributes = triad
        print "%s %s" % (" " * (ix*4), entity)

#################################################################################################

def showAttributes(attributes):
    required = []
    optional = []

    for attr in attributes:
        #name   = '%s' % attr[u'Name']   # or use attr[u'ElementName']
        name   = '%s' % attr[u'ElementName']
        a_type = '%s' % attr[u'AttributeType']
        reqd   = 'Required' if attr[u'Required'] else 'Optional'
        rdonly = 'ReadOnly' if attr[u'ReadOnly'] else 'Settable'
        custom = 'Custom'   if attr[u'Custom']   else 'BakedIn'
        hidden = 'Hidden'   if attr[u'Hidden']   else 'Visible'
        allowedValues = attr[u'AllowedValues']
        tank = required if reqd == 'Required' else optional
        info =  "%-32.32s  %-10.10s  %-8.8s  %-8.8s  %-8.8s  %-7.7s   %d" % \
                (name, a_type, reqd, rdonly, custom, hidden, len(allowedValues))
        tank.append(info)

        if len(allowedValues) <= 12:
            for av in allowedValues:
                #print "    %s" % repr(av)
                av_info = "    |%s|" % av[u'StringValue']
                tank.append(av_info)
#        if name == 'Project':
#            for av in allowedValues:
#                print "    %s" % av.Name
#                print "    %s" % repr(av)

    for item in required + optional:
        print item

#################################################################################################

def getHeritage(item, chain):
    """
    """
    if item.Parent:
        chain = getHeritage(item.Parent, chain)
    parent = item.Parent.ElementName if item.Parent else item.Parent
    chain.append((parent, item.ElementName, item.Attributes))
    
    return chain

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
