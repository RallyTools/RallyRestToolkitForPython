#!/usr/bin/env python
#################################################################################################
#
# updtag.py - example of how to effect an update to an existing tag
#                this script changes the name for a specific Tag
#
USAGE = """\
Usage: python updtag.py <old_tag_name> <new_tag_name>
"""
#################################################################################################

import sys, os

from pyral import Rally, rallyWorkset, RallyRESTAPIError

#################################################################################################

errout = sys.stderr.write

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, user, password, apikey, workspace, project = rallyWorkset(options)
    rally = Rally(server, user, password, apikey=apikey, workspace=workspace)
    rally.enableLogging("rally.history.updtag")

    if len(args) != 2:
        print(USAGE)
        sys.exit(1)

    target_name, new_name = args[:2]
    target_oid = None

    response = rally.get('Tag', fetch="true", order="Name", server_ping=False, isolated_workspace=True)
    for tag in response:
        print("Workspace %s  has tag: %-14.14s created on %s  Name: %s"  % \
              (tag.Workspace.Name, tag.oid, tag.CreationDate[:-5].replace('T', ' '), tag.Name))
        if tag.Name == target_name:
            target_oid = tag.oid

    if not target_oid:
        print("No Tag exists with a Name value of |%s|" % target_name)
        sys.exit(1)

    info = {"ObjectID" : target_oid, "Name" : new_name }
    print(info)
    
    print("attempting to update Tag with Name of '%s' to '%s' ..." % (target_name, new_name))
    try:
        tag = rally.update('Tag', info)
    except RallyRESTAPIError, details:
        sys.stderr.write('ERROR: %s \n' % details)
        sys.exit(2)

    print("Tag updated")
    print("ObjectID: %s  Name: %s  " % (tag.oid, tag.Name))

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)

