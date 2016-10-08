#!/usr/bin/env python

#################################################################################################
#
#  defrevs -- show the revisions for a specific defect
#
USAGE = """
python defrevs [CONFIG] <Defect_FormattedID>

   where CONFIG is either command line arguments or the 
   specification of a file containing pyral related config info
"""
#################################################################################################

import sys, os
from pyral import Rally, rallyWorkset

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, username, password, apikey, workspace, project = rallyWorkset(options)
    rally = Rally(server, username, password, apikey=apikey, workspace=workspace, project=project)
    
    target   = args.pop(0)
    fields   = "FormattedID,State,Name,CreationDate,RevisionHistory,Revisions"
    criteria = "FormattedID = %s" % target 

    defect = rally.get('Defect', fetch=fields, query=criteria, instance=True)

    print("%s  %10.10s  %-11s  %s" % (defect.FormattedID, defect.CreationDate, 
                                      defect.State, defect.Name))
    print("")
    for rev in reversed(defect.RevisionHistory.Revisions):
        print("%d) %-22.22s %-16.16s %s\n" % \
              (rev.RevisionNumber, rev.CreationDate.replace('T', ' '), 
               rev.User.DisplayName, rev.Description))

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)
