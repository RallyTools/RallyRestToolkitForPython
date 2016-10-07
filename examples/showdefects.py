#!/usr/bin/env python

#################################################################################################
#
#  showdefects -- show defects in a workspace/project conforming to some common criterion
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
    if apikey:
        rally = Rally(server, apikey=apikey, workspace=workspace, project=project)
    else:
        rally = Rally(server, user=username, password=password, workspace=workspace, project=project)
    rally.enableLogging("rally.history.showdefects")
    
    fields    = "FormattedID,State,Name,Severity,Priority"
    criterion = 'State != Closed'

    response = rally.get('Defect', fetch=fields, query=criterion, order="FormattedID",
                                   pagesize=200, limit=400)

    for defect in response:
        print("%-8.8s  %-52.52s  %s" % (defect.FormattedID, defect.Name, defect.State))

    print("-----------------------------------------------------------------")
    print(response.resultCount, "qualifying defects")

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)
