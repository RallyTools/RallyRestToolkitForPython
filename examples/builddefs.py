#!/usr/bin/env python

##################################################################################################
#
# builddefs.py -  get build defs for a workspace/project context
#
USAGE = """
Usage: python builddefs.py 
"""
##################################################################################################

import sys, os

from pyral import Rally, rallyWorkset

##################################################################################################

# BUILD_DEFINITION
#Creation Date         DATE        Required  ReadOnly
#Object ID             INTEGER     Required  ReadOnly
#Name                  STRING      Required  Settable
#Project               OBJECT      Required  Settable
#Subscription          OBJECT      Optional  ReadOnly
#Workspace             OBJECT      Optional  Settable
#Description           STRING      Optional  Settable
#Builds                COLLECTION  Optional  ReadOnly
#LastBuild             OBJECT      Optional  ReadOnly
#LastStatus            STRING      Optional  ReadOnly
#Projects              COLLECTION  Optional  Settable
#Uri                   STRING      Optional  Settable


# load up with Workspace / Project combinations appropriate for your environment
#wps = [ ('Fluffy Bunny', 'Jasperex'),
#        ('Hoonerville',  'Engine Parts'),
#        ('BurntNoodles', 'Farina'),
#      ]

wps = [('WHuffaovc', 'Progicbadf')]  # pronounced "dubya-peas" for Workspace-Projects

##################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]

    server, username, password, apikey, workspace, project = rallyWorkset(options)
    if apikey:
        rally = Rally(server, apikey=apikey, workspace=workspace)
    else:
        rally = Rally(server, user=username, password=password, workspace=workspace)
    rally.enableLogging("rally.history.blddefs")

    for workspace, project in wps:
        rally.setWorkspace(workspace)
        print("workspace: %s  project: %s\n" % (workspace, project))
        response = rally.get('BuildDefinition', fetch=True, 
                             query='Project.Name = "%s"' % project, 
                             order='Name', workspace=workspace, project=project)
        if response.errors:
            print(response.errors)
            sys.exit(9)

        print("%-12.12s   %-10.10s  %-36.36s %12s  %-20.20s  %s" % \
              ('BuildDef OID', 'CreateDate', 'BuildDefinition.Name', 'LastStatus', 'LastBuildDateTime', 'NumBuilds'))
        print("%-12.12s   %-10.10s  %-36.36s   %10s  %-19.19s   %s" % \
              ('-' * 12, '-' * 10, '-' * 36, '-' * 10, '-' * 19, '-' * 9))
        for builddef in response:
            if builddef.LastStatus == "NO BUILDS":
                print("%s %s %-24.24s NO BUILDS" % \
                      (builddef.oid, builddef.CreationDate[:10], builddef.Name))
                continue
            lbt = builddef.LastBuild.CreationDate.split('T')
            last_build_time = "%s %s" % (lbt[0], lbt[1][:8] )
            bdf = "%12.12s   %-10.10s  %-36.36s %12s  %-20.20s    %4s"
            print(bdf % (builddef.oid, builddef.CreationDate[:10], 
                  builddef.Name, builddef.LastStatus, last_build_time,
                  len(builddef.Builds)))

##################################################################################################
##################################################################################################

if __name__ == "__main__":
    main(sys.argv[1:])
