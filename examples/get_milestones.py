#!/usr/bin/env python

#################################################################################################
#
# getmilestones.py -- Get all of the Milestone items for the specified scope
#                     and print them in TargetProject.Name, TargetDate order
#
USAGE = """
Usage: getmilestones.py   
"""
#################################################################################################

import sys

from pyral import Rally, rallyWorkset

#################################################################################################

errout = sys.stderr.write

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, user, password, apikey, workspace, project = rallyWorkset(options)
    rally = Rally(server, user, password, apikey=apikey, workspace=workspace, project=project)

    entity_name = 'Milestone'
    fields      = 'FormattedID,Name,TargetProject,TargetDate,TotalArtifactCount'
    response = rally.get(entity_name, fetch=fields, order="TargetDate,FormattedID", 
                         project=project, projectScopeDown=True)

    if response.errors:
        errout("Request could not be successfully serviced, error code: %d\n" % response.status_code)
        errout("\n".join(response.errors))
        sys.exit(1)

    if response.resultCount == 0:
        errout('No items found for %s\n' % entity_name)
        sys.exit(2)

    milestones = [item for item in response]
    sans_project = [mi for mi in milestones if not mi.TargetProject]
    with_project = [mi for mi in milestones if     mi.TargetProject]
    with_project.sort(key=lambda mi: mi.TargetProject.Name)

    for item in (with_project + sans_project):
        proj_name = item.TargetProject.Name if item.TargetProject else ""
        print(" %15.15s  %-6.6s  %-36.36s  %3d  %-10.10s  %s " % \
                 (item.oid, item.FormattedID, item.Name, 
                  item.TotalArtifactCount, item.TargetDate, proj_name))

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
