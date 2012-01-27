#!/usr/bin/env python

#################################################################################################
#
#  periscope.py -- Show all workspaces and projects available to the logged in user
#
#################################################################################################

import sys, os

from pyral import Rally, rallySettings

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, username, password, workspace, project = rallySettings(options)
    #print "|%s| |%s| |%s| |%s| |%s|" % (server, username, password, workspace, project)
    print "|%s| |%s| |%s| |%s| |%s|" % (server, username, '********', workspace, project)
    rally = Rally(server, username, password)     # specify the Rally server and credentials
    rally.enableLogging('rally.hist.periscope')  # name of file for logging content

    for workspace in rally.getWorkspaces():
        print "%s %s" % (workspace.oid, workspace.Name)
        for project in rally.getProjects(workspace=workspace.Name):
            print "    %12.12s  %s" % (project.oid, project.Name)

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])

