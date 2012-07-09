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

from pyral import Rally, rallySettings

##################################################################################################

# BUILD_DEFINITION
#Creation Date         DATE        Required  ReadOnly  BakedIn   Visible
#Object ID             INTEGER     Required  ReadOnly  BakedIn   Visible
#Name                  STRING      Required  Settable  BakedIn   Visible
#Project               OBJECT      Required  Settable  BakedIn   Visible
#Subscription          OBJECT      Optional  ReadOnly  BakedIn   Visible
#Workspace             OBJECT      Optional  Settable  BakedIn   Visible
#Description           STRING      Optional  Settable  BakedIn   Visible
#Builds                COLLECTION  Optional  ReadOnly  BakedIn   Visible
#LastBuild             OBJECT      Optional  ReadOnly  BakedIn   Visible
#LastStatus            STRING      Optional  ReadOnly  BakedIn   Visible
#Projects              COLLECTION  Optional  Settable  BakedIn   Visible
#Uri                   STRING      Optional  Settable  BakedIn   Visible


# load up with Workspace / Project combinations appropriate for your environment
#wps = [ ('Fluffy Bunny', 'Jasperex'),
#        ('Hoonerville',  'Engine Parts'),
#        ('BurntNoodles', 'Farina'),
#      ]

wps = [('WHuffaovc', 'Progicbadf')]  # pronounced "dubya-peas" for Workspace-Projects

##################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]

    server, user, password, workspace, project = rallySettings(options)
    rally = Rally(server, user, password, workspace=workspace)
    rally.enableLogging("rally.history.blddefs")

    for workspace, project in wps:
        print "workspace: %s  project: %s" % (workspace, project)
        rally.setWorkspace(workspace)
        response = rally.get('BuildDefinition', fetch=True, 
                             order='Name',
                             workspace=workspace, 
                             project=project)
        if response.errors:
            print response.errors
            sys.exit(9)

        for builddef in response:
            if builddef.Project.Name != project:
                continue
            if builddef.LastStatus == "NO BUILDS":
                print "NO BUILDS"
                continue
            #print builddef.oid, builddef.Name, builddef.LastStatus
            lbt = builddef.LastBuild.CreationDate.split('T')
            last_build_time = "%s %s" % (lbt[0], lbt[1][:5] )
            bd_name = "%-24.24s" % builddef.Name
            status  = "%-10.10s" % builddef.LastStatus
            print builddef.oid, builddef.CreationDate[:10], \
                  bd_name, status, last_build_time, len(builddef.Builds)

        print "\n"

##################################################################################################
##################################################################################################

if __name__ == "__main__":
    main(sys.argv[1:])
