#!/usr/bin/env python

#################################################################################################
#
#  repoitems.py - show changesets associated with a particular repository
#
USAGE = """
Usage: python repoitems.py <repository_name>
"""
#################################################################################################

__doc__ = """
    A Changeset item has these attributes:
        ObjectID
        CreationDate
        Name
        Subscription
        Workspace
        SCMRepository
        Revision
        CommitTimestamp
        Author
        Message
        Changes
        Artifacts
        Builds
"""

#################################################################################################

import sys, os
import time

from pyral import Rally, rallyWorkset

#################################################################################################

ITEM_LIMIT = 1000

errout = sys.stderr.write

oid_cache = {}

#################################################################################################

def main(args):

    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    if not args:
        print  USAGE
        sys.exit(9)
    server, username, password, apikey, workspace, project = rallyWorkset(options)
    if apikey:
        rally = Rally(server, apikey=apikey, workspace=workspace, project=project)
    else:
        rally = Rally(server, user=username, password=password, workspace=workspace, project=project)
    rally.enableLogging('rally.hist.chgsets')  # name of file you want the logging to go to

    repo_name = args.pop(0)
    since = None
    if args:
        since = args.pop(0)
        try:
            days = int(since)
            now = time.time()
            since_ts = now - (days * 86400)
            since = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(since_ts))
        except:
            since = None

    showRepoItems(rally, repo_name, workspace=workspace, limit=ITEM_LIMIT, since_date=since)

#################################################################################################

def showRepoItems(rally, repo_name, workspace=None, limit=200, order="ASC", since_date=None):
    
    by_repo = 'SCMRepository.Name = "%s"' % repo_name
    criteria = by_repo
    if since_date:
        date_cond = "CommitTimestamp >= %s" % since_date
        criteria = "((%s) and (%s))" % (by_repo, date_cond)


    try:
        response = rally.get('Changeset', fetch=True, 
                             order="CommitTimestamp %s" % order,
                             query=criteria,
                             workspace=workspace, project=None, 
                             pagesize=200, limit=limit)
    except Exception, msg:
        print msg
        return None

    if response.errors:
        errout("Changeset request could not be successfully serviced, error code: %d\n" % \
               response.status_code)
        return None

    print "Workspace: %s  SCMRepository: %s  Changesets: %s " % \
          (workspace, repo_name, response.resultCount)
    for cs in response:
        author    = cs.Author.UserName if cs.Author else "-None-"
        committed = cs.CommitTimestamp.replace('T', ' ')

        print "%-12.12s  %-42.42s %-19.19s Z %s  %s" % \
              (cs.SCMRepository.Name, cs.Revision, committed, author, cs.oid)
        print "         |%s|" % cs.Message

        # If we iterate over change items via cs.Changes, then we later have to do lazy load
        # for the change attributes on a per Change basis, which is relatively slow
        # So, instead we go get all Change items associated with the Changeset
        # and get the Change attributes populated, so we don't do a lazy load
#        changes = rally.get('Change', fetch='Action,PathAndFilename,Changeset', 
#                             query="Changeset = %s" % cs.ref,
#                             workspace=workspace, project=None, 
#                             pagesize=200, limit=limit)
#        for change in changes:
#            print "      %s  %s" % (change.Action, change.PathAndFilename)

        if len(cs.Artifacts) == 0:
            #print "changeset %s - %s has no artifacts"  % (cs.SCMRepository.Name, cs.Revision)
            continue

        artifact_idents = []
        for shell_artifact in cs.Artifacts:
            entity = shell_artifact._type # the shell artifact has the oid, not the FormattedID
            if shell_artifact.oid not in oid_cache:
                by_oid = "ObjectID = %s" % shell_artifact.oid
                art_response = rally.get(entity, fetch="FormattedID", query=by_oid)
                if art_response.resultCount == 1:
                    art = art_response.next()
                    oid_cache[shell_artifact.oid] = art
            artifact = oid_cache.get(shell_artifact.oid, None)
            if artifact:
                artifact_idents.append(artifact.FormattedID)
        if artifact_idents:
            print "         artifacts mentioned: %s" % " ".join(artifact_idents)

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
