#!/usr/bin/env python3

#################################################################################################
#
#  periscope.py -- Show all workspaces and projects available to the logged in user
#
#################################################################################################

USAGE = """
Usage: python3 periscope.py {--conf=<your.cfg>} {workspace=NN workspace=WW ...} {project=PP}
"""

#################################################################################################

import sys, os

from pyral import Rally, rallyWorkset

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    wksp_specs = [arg for arg in args if arg.startswith('workspace=')]
    proj_specs = [arg for arg in args if arg.startswith('project=')]
    if wksp_specs:
        specific_workspaces = [wkspec.split('=')[1]  for wkspec  in wksp_specs]
    else:
        specific_workspaces = []
    if proj_specs:
        specific_projects   = [prjspec.split('=')[1] for prjspec in proj_specs]
    else:
        specific_projects   = []

    server, username, password, apikey, workspace, project = rallyWorkset(options)

    iso = False
    if specific_workspaces and len(specific_workspaces) == 1:
        workspace = specific_workspaces[0]
        iso = True

    if apikey:
        rally = Rally(server, apikey=apikey, workspace=workspace, project=project, 
                      isolated_workspace=iso)
    else:
        rally = Rally(server, user=username, password=password, workspace=workspace, 
                      project=project, isolated_workspace=iso)
    #rally.enableLogging('rally.hist.periscope')  # name of file for logging content

    if not iso:
        workspaces = rally.getWorkspaces()
    else:
        workspaces = [rally.getWorkspace()]
    if specific_workspaces and not iso:
        workspaces = [wksp for wksp in workspaces if wksp.Name in specific_workspaces ]

    for workspace in workspaces:
        print("%s %s" % (workspace.oid, workspace.Name))
        # looking for Workspace OID of 33936922066
        projects = rally.getProjects(workspace=workspace.Name)
        if specific_projects:
            projects = [proj_name for proj_name in specific_projects if proj_name in projects]
        for project in projects:
            print(f"    {project.oid:<12}  {project.Name:<36.36}   |{project.State}|")
        print("")

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])

