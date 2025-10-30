#!/usr/bin/env python

#################################################################################################
#
# get_iterations.py -- Get some of the Iteration items for the specified scope
#                      and print them in TargetProject.Name, StartDate, EndDate order,
#                      Limit the number of Iteration items retrieved to the limit argument
#                      
#
USAGE = """
Usage: get_iterations.py  <limit> 
"""
#################################################################################################

import sys,os
import re

from pyral import Rally, rallyWorkset

#################################################################################################

errout = sys.stderr.write

LIMIT = 100

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    if args and re.match(r'^\d+$', args[0]):
        limit = int(args[0])
    else:
        limit = LIMIT
        if args:
            print(f"WARNING: Your limit argument value of '{args[0]}' is not a number, defaulting to {LIMIT}")
    server, user, password, apikey, workspace, project = rallyWorkset(options)
    rally = Rally(server, user, password, apikey=apikey, workspace=workspace, project=project)

    entity_name = 'Iteration'
    fields      = 'Name,StartDate,EndDate,State,Project'
    response = rally.get(entity_name, fetch=fields, order="Project.Name,StartDate,EndDate", 
                         project=project, projectScopeDown=True, 
                         pagesize=10,limit=limit)

    if response.errors:
        errout("Request could not be successfully serviced, error code: %d\n" % response.status_code)
        errout("\n".join(response.errors))
        sys.exit(1)

    if response.resultCount == 0:
        errout('No items found for %s\n' % entity_name)
        sys.exit(2)

    print(f'Query shows resultCount as {response.resultCount}')

    for ix, iteration in enumerate(response):
        num = ix+1
        proj_name = iteration.Project.Name if iteration.Project else ""
        sd = iteration.StartDate.split('T')[0]
        ed = iteration.EndDate.split('T')[0]
        irec = f'{num}  {proj_name:24}  {iteration.Name:<33.30} {sd}   {ed}   {iteration.State}'
        print(irec)


#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
