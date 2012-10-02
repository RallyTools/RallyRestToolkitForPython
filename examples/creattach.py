#!/usr/bin/env python

#################################################################################################
#
# creattach.py -- Associate a file with an Artifact as an Attachment
#
USAGE = """
Usage: py creattach.py <ArtifactIdentifier> <filename>
"""
#################################################################################################

import sys, os
import re
import string

from pyral import Rally, rallySettings

#################################################################################################

errout = sys.stderr.write

ARTY_FOR_PREFIX = {'S' : 'UserStory', 'US' : 'UserStory', 'DE' : 'Defect', 'TC' : 'TestCase'}

ATTACHMENT_ATTRIBUTES = ['oid', 'ObjectID', '_type', '_ref', '_CreatedAt', 'Name',
                         'CreationDate', 'Description', 
                         'Content', 'ContentType', 'Size', 
                         'Subscription', 
                         'Workspace',
                         'Artifact', 
                         'User'
                        ] 

ATTACHMENT_IMPORTANT_ATTRS = """
    Subscription   ref     (supplied at creation)
    Workspace      ref     (supplied at creation)

    Name           STRING      Required    (name of the file, like foo.txt or ThePlan.doc)
    User           ref to User Required   Settable  (User who added the object)

    Content        ref to AttachmentContent
    Size           INTEGER     Required
    ContentType    STRING      Required


    Artifact       ref to Artifact            (optional field)

    Description    TEXT        Optional
        
"""

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, user, password, workspace, project = rallySettings(options)
    print " ".join(["|%s|" % item for item in [server, user, '********', workspace, project]])
    rally = Rally(server, user, password, workspace=workspace, version="1.30")  # specify the Rally server and credentials
    rally.enableLogging('rally.hist.creattach') # name of file you want logging to go to

    if len(args) != 2:
        errout('ERROR: You must supply an Artifact identifier and an attachment file name')
        errout(USAGE)
        sys.exit(1)

    target, attachment_file_name = args
    artifact = validateTarget(rally, target)

    me = rally.getUserInfo(username=user).pop(0)
    #print "%s user oid: %s" % (user, me.oid)

    att = rally.addAttachment(artifact, attachment_file_name)
    print "created Attachment: %s for %s" % (attachment_file_name, target)

#################################################################################################

def validateTarget(rally, target):
    mo = re.match('^(S|US|DE|TC)\d+$', target)
    if not mo:
        errout("Target artifact identification flawed, invalid FormattedID value\n")
        sys.exit(2)
    prefix = mo.group(1)
    entity = ARTY_FOR_PREFIX.get(prefix, None)
    if not entity:
        errout("Target artifact identification flawed, unknown prefix: %s\n" % prefix)
        sys.exit(3)

    ident_query = 'FormattedID = %s' % target
    response = rally.get(entity, fetch=True, query=ident_query, project=None)

    if response.errors:
        errout("Request could not be successfully serviced, error code: %d\n" % response.status_code)
        errout("\n".join(response.errors))
        sys.exit(4)

    if response.resultCount == 0:
        errout('No item found for %s %s\n' % (entity, target))
        sys.exit(5)
    elif response.resultCount > 1:
        errout('ERROR: more than 1 item returned matching your criteria for the target\n')
        sys.exit(6)
    
    artifact = response.next()

    return artifact

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])

