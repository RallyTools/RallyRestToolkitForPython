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
ATTRIBUTE_FIELDS = "ElementName,Parent,Attributes,AttributeType,Abstract,Required," +\
                   "Queryable,ReadOnly,Deletable,Hidden,Custom,Filterable," +\
                   "MaxLength,AllowedValues"

errout = sys.stderr.write

CAMEL_CASED_NAME_PATT = re.compile('([a-z])([A-Z][a-z])')

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
     u'Name', 
     u'ElementName', 
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

    query = ""
    if args:
        target = args[0]
        if target in ['UserStory', 'User Story', 'Story']:
            target = "HierarchicalRequirement"
        mo = CAMEL_CASED_NAME_PATT.search(target)
        if mo:
            txfm = re.sub(CAMEL_CASED_NAME_PATT, r'\1 \2', target)
            print 'transforming query target "%s" to "%s"' % (target, txfm)
            target = txfm
            
        query = 'Name = "%s"' % target

    try:
        rally = Rally(server, user=user, password=password)
    except Exception, msg:
        stuff = sys.exc_info
        errout(stuff)
        errout(str(msg))       
        sys.exit(1)

    response = rally.get('TypeDefinition', fetch=ATTRIBUTE_FIELDS, query=query, pretty=True)
    if response.errors:
        errout("Request could not be successfully serviced, error code: %d\n" % response.status_code)
        errout("\n".join(response.errors))
        sys.exit(1)

    tdd = response.content
    results = response.content[u'QueryResult'][u'Results']
    tdd = results[0]

    showAttributes(tdd[u'Attributes'])

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
        name   = '%s' % attr[u'Name']   # or use attr[u'ElementName']
        a_type = '%s' % attr[u'AttributeType']
        reqd   = 'Required' if attr[u'Required'] else 'Optional'
        rdonly = 'ReadOnly' if attr[u'ReadOnly'] else 'Settable'
        custom = 'Custom'   if attr[u'Custom']   else 'BakedIn'
        hidden = 'Hidden'   if attr[u'Hidden']   else 'Visible'
        allowedValues = attr[u'AllowedValues']
        tank = required if reqd == 'Required' else optional
        info =  "%-20.20s  %-10.10s  %-8.8s  %-8.8s  %-8.8s  %-7.7s   %d" % \
                (name, a_type, reqd, rdonly, custom, hidden, len(allowedValues))
        tank.append(info)

        if len(allowedValues) <= 12:
            for av in allowedValues:
                #print "    %s" % repr(av)
                av_info = "    |%s|" % av[u'StringValue']
                tank.append(av_info)
        if name == 'Project':
            for av in allowedValues:
                print "    %s" % repr(av)

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
