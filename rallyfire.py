#!/usr/bin/env python

#################################################################################################
#
#  rallyfire - Exemplar script to test the basic connectivity to a Rally server
#              and obtain basic workspace and project information
#
#              Look at the blocks of text in the main function to see how you can
#              obtain a Rally instance using auth of user/password or apikey
#              along with workspace / project values and whether or not you want to
#              get an instance that covers only a single workspace.
#              Experiment with those instantiations to find one that works well for
#              your situation.
#
#################################################################################################

import sys
print("\n".join(sys.path))

from pyral import Rally, rallyWorkset

#################################################################################################

errout = sys.stderr.write

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, user, password, apikey, workspace, project = rallyWorkset(options)
    #print(f" |{server}| |{user}| |{password}| |{apikey[:8]}| |{workspace}| |{project}|")

    # If you want to use BasicAuth, use the following form
    #rally = Rally(server, user, password, workspace=workspace, project=project)

    # If you want to use API Key, you can use the following form
    #rally = Rally(server, apikey=apikey, workspace=workspace, project=project,
    #              isolated_workspace=True)
    #rally = Rally(server, apikey=apikey, workspace=workspace, project=project)

    # the following form of obtaining a Rally instance will use the apikey if it is present (non None)
    # otherwise it will use the user and password for BasicAuth
    # add in the debug=True keyword arg pair if you want more verbiage ...
    #apikey = "some valid apikey value"
    #rally = Rally(server, apikey=apikey)

    rally = Rally(server, user, password, apikey=apikey,
                  workspace=workspace, project=project,
                  debug=True, isolated_workspace=True)
    specified_workspace = workspace

    workspace = rally.getWorkspace()
    print(f"Workspace: {workspace.Name}   id: {workspace.oid} ")
    #if specified_workspace != workspace.Name:
    #    print(f"    ** The workspace you specified: {specified_workspace} is not a valid workspace name for your account, using your default workspace instead")
    #print "Workspace: {workspace.oid:<12}   %{workspace.Name:<18.18}    ({workspace.ref})")

    project = rally.getProject()
    print(f"Project: {project.Name}   id: {project.oid} ")

    #
    # issue a call to rally.getProjects() to see where you might be able to
    # monkey with the current context's workspace (Name and oid) to be able
    # to alter it to identify this workspace 'General Tsao's Alt Sandbox'
    #  https://rally1.rallydev.com/#/9095683773d/detail/workspace/9096107191
    #
    # alt_workspace = "General Tsao's Alt Sandbox"
    #print(f"Obtaining Projects for alternate Workspace: {alt_workspace}")
    #projects = rally.getProjects(workspace=alt_workspace)
    #for proj in projects:
    #    print(f'Project Name: {proj.Name}   ObjectID: {proj.oid}')

    # Uncomment the following function call to see all of your accessible workspaces and projects.
    # Be aware that if you are in a subscription with a lot of workspaces and projects
    # this could take a lot longer than you want it to. 
    #    (consider using isolated_workspace=True in rally = Rally(...., isolated_workspace=True) )
    #showWorkspacesAndProjects(rally)

#################################################################################################

def showWorkspacesAndProjects(rally):
    workspaces = rally.getWorkspaces()
    for workspace in workspaces:
        print(" ", workspace.Name)
        projects = rally.getProjects(workspace=workspace.Name)
        if projects:
            print("")
            print("    Projects:")
            for project in projects:
                print("     ", project.Name)
        else:
            print("  No projects")
        print("")

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)
