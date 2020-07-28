import sys, os

from pyral import Rally, rallyWorkset, RallyRESTAPIError

server   = 'demo-west.rallydev.com'
username = 'jpkole@rallydev.com'
authy    = 'Kanban!!'

foozy_workspace = 'Workspace #1'
std_project     = 'Online Store'

rally = Rally(server, username, authy, workspace=foozy_workspace, project=std_project)
#print(rally)

#my_workspace  = 'zJP-Test-WS-1'
#valid_project = 'Sample Project'
#rally2 = Rally(server, username, authy, workspace=my_workspace, project=valid_project)
#print(rally2)

#for my_workspace in ['zJP-Test-WS-1']:
#    print ("Connecting to Workspace: '%s'" % my_workspace)
    ##print ("Connecting to Rally ...    not specifying a Workspace/Project combo")
    #try:
    #    #rally = Rally(server, username, authy, workspace=my_workspace, project="Online Store")
    #    rally = Rally(server, username, authy, workspace=my_workspace)
    #    #rally = Rally(server, username, authy)
    #except RallyRESTAPIError as ex:
    #    print(ex)
    #    sys.exit(1)

#    current_workspace = rally.getWorkspace()
#    print(current_workspace.Name)
#
#    projects = rally.getProjects()
#    for project in projects:
#        print("    %s"  % project.Name)
#
#    print ("\tsuccess!")
#    #rally.setProject("Online Store")
#
#    break
#
#
all_workspaces = rally.getWorkspaces()
print(" All Workspaces ...")
for wksp in all_workspaces:
    print(wksp.Name)

#wacky_workspace_1 = 'Workspace #1'
#rally.setWorkspace(wacky_workspace_1)
#current_workspace = rally.getWorkspace()
#print("\n\nset the workspace to %s" % current_workspace.Name)
#wacky_projects = rally.getProjects()
#for proj in wacky_projects:
#    print("    %s" % proj.Name)