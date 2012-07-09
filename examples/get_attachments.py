#!/usr/bin/env python

#################################################################################################
#
# get_attachments.py -- Get the the contents of all of attachments associated with a 
#                       specific instance of a Rally type identified either by an OID 
#                       or a FormattedID value
#
USAGE = """
Usage: py get_attachments <entity_name> <OID | FormattedID> 
"""
#################################################################################################

import sys
import re
import string

from pyral import Rally, rallySettings

#################################################################################################

errout = sys.stderr.write

STORY_ALIASES = ['Story', 'UserStory', 'User Story']

OID_PATT          = re.compile(r'^\d+$')
FORMATTED_ID_PATT = re.compile(r'[A-Z]+\d+')

COMMON_ATTRIBUTES = ['_type', 'oid', '_ref', '_CreatedAt', '_hydrated', 'Name']

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, user, password, workspace, project = rallySettings(options)
    print " ".join(["|%s|" % item for item in [server, user, '********', workspace, project]])
    rally = Rally(server, user, password, workspace=workspace)
    rally.enableLogging('rally.hist.getattachs') # name of file you want logging to go to

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

    artifact = response.next()
    attachments = rally.getAttachments(artifact)
    for attachment in attachments:
        print "-" * 32
        print attachment.Name
        print "~" * len(attachment.Name)
        print attachment.Content
        print ""
        print "=" *  64

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
