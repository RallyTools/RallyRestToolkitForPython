#!/usr/bin/env python

#################################################################################################
#
#  showdefects -- show defects in a workspace/project conforming to some common criterion
#
#################################################################################################

import sys, os

from pyral import Rally, rallySettings, RallyRESTAPIError

#################################################################################################

errout = sys.stderr.write

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, user, password, workspace, project = rallySettings(options)
    rally = Rally(server, user, password, workspace=workspace, project=project)
    rally.enableLogging("rally.history.showdefects")
    
    fields    = "FormattedID,State,Name,Severity,Priority", 
    criterion = 'State != Closed'

    response = rally.get('Defect', fetch=fields, query=criterion, order="FormattedID",
                                   pagesize=200, limit=400)

    for defect in response:
        print "%-6.6s  %-46.46s  %s" % (defect.FormattedID, defect.Name, defect.State)

    print "-----------------------------------------------------------------"
    print response.resultCount, "qualifying defects"

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)
