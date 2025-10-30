#!/usr/bin/env python

#################################################################################################
#
#  cr_milestone.py -- Create a Milestone instance with a Name and TargetDate
#
USAGE = """
Usage: cr_milestone.py  <name> <target_date>
"""
#################################################################################################

import sys, os
from pyral import Rally, rallyWorkset

#################################################################################################

errout = sys.stderr.write

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]

    if len(args) != 2:
        print("No arguments for the Milestone Name or TargetDate were specified")
        sys.exit(1)

    server, user, password, apikey, workspace, project = rallyWorkset(options)
    if apikey:
        rally = Rally(server, apikey=apikey, workspace=workspace, project=project)
    else:
        rally = Rally(server, user=user, password=password, workspace=workspace, project=project)

    target_project = rally.getProject()
    target_entity_name    = 'Milestone'
    milestone_name, milestone_target_date = args[:2]
    info = { 'Name'       : milestone_name,
             'TargetDate' : milestone_target_date
           }


    print(f"Creating {target_entity_name} ...")
    milestone = rally.put(target_entity_name, info)
    print(f"Created  Milestone: {milestone.FormattedID}   OID: {milestone.oid}  Name: {milestone.Name}  TargetDate: {milestone.TargetDate}")

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
