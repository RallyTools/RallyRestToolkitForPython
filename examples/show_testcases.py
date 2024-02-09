#!/usr/bin/env python

#################################################################################################
#
#  showtestcases -- show TestCases in a specific workspace
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
    #rally.enableLogging("rally.history.show_testcases")
    
    fields = "FormattedID,Name,Description,LastRun,LastVerdict,Results,Type,CreationDate,TestSets"

    response = rally.get('TestCase', fetch=fields, 
                                   pagesize=200, limit=400)

    for tc in response:
        print("%-8.8s  %-32.32s  %-12.12s  %-12.12s  %-8.8s  %s" % \
             (tc.FormattedID, tc.Name, tc.Type, tc.LastRun, tc.LastVerdict, tc.ref))
        print(tc.details())
        print(tc.TestSets)
        #print("")
        for ts in tc.TestSets:
            print("   %-6.6s  %-24.24s  %s" % (ts.FormattedID, ts.Name, ts.oid))
        print("")

    print("-----------------------------------------------------------------")
    print(response.resultCount, "qualifying TestCases")

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)
