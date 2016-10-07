#!/usr/local/bin/python2.7

#################################################################################################
#
#  get_schedulable_artifacts.py - experimental script to retrieve information about all
#                                 schedulable artifacts in a particular project
#
USAGE = """
Usage: py get_schedulable_artifacts.py
"""
#################################################################################################

import sys, os

from pyral import Rally, rallyWorkset

#################################################################################################

errout = sys.stderr.write


PROJECTS = ['some project 1', 'another project x']

#################################################################################################

def main(args):

    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, username, password, apikey, workspace, project = rallyWorkset(options)
    rally = Rally(server, username, password, apikey=apikey, workspace=workspace)
    wksp = rally.getWorkspace()
    print("Workspace: %s" % wksp.Name)
    print("=" * (len(wksp.Name) + 12))
    print("")

    for project in PROJECTS:
        rally.setProject(project)
        print("  %s" % project)
        print("  %s" % ('-' * len(project)))
        print("")
        response = getSchedulableArtifacts(rally)
        showSchedulableArtifacts(response)
        print("")
        print("-" * 80)
        print("")
        print("%d items" % response.resultCount)
        print("")

#################################################################################################

def getSchedulableArtifacts(rally):
    response = rally.get('SchedulableArtifact', 
                         fetch="ObjectID,FormattedID,Name,AcceptedDate,Project,Release,Iteration",
                         order='AcceptedDate',
                         projectScopeUp=False,
                         projectScopeDown=False,
                         pagesize=100, limit=5000)

    if response.errors:
        errout("Request could not be successfully serviced, error code: %d\n" % response.status_code)
        errout("\n".join(response.errors))
        sys.exit(1)

    return response

#################################################################################################

def showSchedulableArtifacts(items):
    for sched_art in items:
        release   = ""
        iteration = ""
        accepted  = ""
        if sched_art._type != 'PortfolioItem' and sched_art._type != 'TestCase':
            release   = sched_art.Release.Name   if sched_art.Release   else ""
            iteration = sched_art.Iteration.Name if sched_art.Iteration else ""
            accepted  = sched_art.AcceptedDate   if hasattr(sched_art, 'AcceptedDate') else ""
        print("    %-7.7s  %-64.64s   %-12.12s   %16.16s   %s" % \
                  (sched_art.FormattedID, sched_art.Name, release, iteration, accepted))

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
