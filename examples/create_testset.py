#!/usr/bin/env python

#################################################################################################
#
#  create_testset -- create a TestSet in a specific workspace and project
#
#################################################################################################

import sys, os
from pyral import Rally, rallyWorkset, RallyRESTAPIError

#################################################################################################

errout = sys.stderr.write

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, username, password, apikey, workspace, project = rallyWorkset(options)
    #if apikey:
    #    rally = Rally(server, apikey=apikey, workspace=workspace, project=project)
    #else:
    #    rally = Rally(server, user=username, password=password, workspace=workspace, project=project)
    rally = Rally(server, user=username, password=password, workspace=workspace, project=project)
    rally.enableLogging("rally.history.show_testsets")
    
    fields = "FormattedID,Name,Description,Release,Iteration,PlanEstimate,ScheduleState,LastBuild,LastRun"
    testset_data \
            = {'Name' : 'Whirlwind Assembly',
               'Description' : 'Run in circles until clarity emerges',
               'Release' : 'release/436901395504',
               'ScheduleState' : 'In-Progress',
          }

    testset = rally.create('TestSet', testset_data)
    print(testset)


#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)
