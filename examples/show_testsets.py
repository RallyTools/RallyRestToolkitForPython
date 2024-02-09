#!/usr/bin/env python

#################################################################################################
#
#  showtestsets -- show TestSets in a specific workspace
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
    #rally.enableLogging("rally.history.show_testsets")
    
    fields = "FormattedID,Name,Description,Release,Iteration,PlanEstimate,ScheduleState,LastBuild,LastRun,TestCases"

    response = rally.get('TestSet', fetch=fields, pagesize=200, limit=400)

    for ts in response:
        print("%-8.8s  %-52.52s  %-12.12s  %-12.12s  %s  %s" % \
             (ts.FormattedID, ts.Name, ts.ScheduleState, ts.LastBuild, ts.LastRun, ts.ref))
        #print(ts.TestCases)
        #print("")
        for tc in ts.TestCases:
            print("   %-6.6s  %-24.24s  %s" % (tc.FormattedID, tc.Name, tc.oid))
        print("-------------------------------------------------------------------------------")
        print()

    print("-----------------------------------------------------------------")
    print(response.resultCount, "qualifying TestSets")

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)
