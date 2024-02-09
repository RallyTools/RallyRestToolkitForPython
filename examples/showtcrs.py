#!/usr/bin/env python

#################################################################################################
#
#  showtcrs -- show TestCaseResults in a workspace/project conforming to some common criterion
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
    #rally.enableLogging("rally.history.showtcrs")
    
    fields = "Build,Date,Duration,Verdict,TestCase,TestSet"

    #criterion = 'Date >= 2020-06-01T00:00:00.000Z'

    response = rally.get('TestCaseResult', fetch=fields, order="Date",
                                           pagesize=200, limit=400)

    for tcr in response:
        print("%-8.8s  %-16.16s  %-12.12s  %-8.8s %-36.36s  %-36.36s" % \
              (tcr.Build, tcr.Date, tcr.Verdict, tcr.TestCase.FormattedID, tcr.TestCase.ref, tcr.TestSet))

    print("-----------------------------------------------------------------")
    print(response.resultCount, "qualifying TestCaseResults")

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)
