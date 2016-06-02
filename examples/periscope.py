#!/usr/bin/env python

#################################################################################################
#
#  periscope.py -- Show all workspaces and projects available to the logged in user
#
#################################################################################################

import sys, os

from pyral import Rally, rallyWorkset

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, username, password, apikey, workspace, project = rallyWorkset(options)
    if apikey:
        rally = Rally(server, apikey=apikey, workspace=workspace, project=project)
    else:
        rally = Rally(server, user=username, password=password, workspace=workspace, project=project)
    rally.enableLogging('rally.hist.periscope')  # name of file for logging content

    for workspace in rally.getWorkspaces():
        print("%s %s" % (workspace.oid, workspace.Name))
        for project in rally.getProjects(workspace=workspace.Name):
            print("    %12.12s  %-36.36s   |%s|" % (project.oid, project.Name, project.State))
        print("")

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])

