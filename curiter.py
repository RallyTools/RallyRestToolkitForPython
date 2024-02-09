#!/usr/bin/env python3

#################################################################################################
#
# curiter.py -- demonstration script to obtain the current iteration 
#               for a particular project
#
#################################################################################################

import sys, os
import time

from pyral import Rally, rallyWorkset

#################################################################################################

errout = sys.stderr.write

#################################################################################################

def main(args):

    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, username, password, apikey, workspace, project = rallyWorkset(options)
    print(" ".join(["|%s|" % item for item in [server, username, password, workspace, project]]))
    if apikey:
        rally = Rally(server, username, apikey=apikey, workspace=workspace, project=project)
    else:
        rally = Rally(server, username, password, workspace=workspace, project=project)

    today = time.strftime("%Y-%m-%d", time.localtime(time.time()))

    response = rally.get('Iteration', 
                         workspace=workspace,
                         fetch="Name,Project,StartDate,EndDate,State,PlannedStartDate,PlannedEndDate",
                         query=[f"StartDate <= {today}", f"EndDate >= {today}"],
                         order="StartDate ASC",
                         projectScopeUp=False, 
                         projectScopeDown=True,
                         pagesize=100, limit=500)

    if response.errors:
        errout("Request could not be successfully serviced, error code: %d\n" % response.status_code)
        errout("\n".join(response.errors))
        sys.exit(1)

    iteration_items = [iteration for iteration in response]
    alphabetic_team_list = sorted(iteration_items, key=lambda x: x.Project.Name)

    for iteration in alphabetic_team_list:
        try:
            projName = iteration.Project.Name if iteration.Project else 'NONE'
        except:
            projName = 'BONK!'
        iterStart = iteration.StartDate.split('T')[0]
        iterEnd   = iteration.EndDate.split('T')[0]
        print(f"{projName:<30.30} {iteration.Name:<24} {iterStart}  {iterEnd}  {iteration.State}")

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
