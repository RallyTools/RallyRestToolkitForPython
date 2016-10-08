#!/usr/bin/env python

#################################################################################################
#
#  add_tcrs.py -- Add TestCaseResult items to a TestCase with information supplied in a text file
#
USAGE = """
Usage: add_tcrs.py <TestCase FormattedID> <tcr_info>[, <tcr_info>, ...]
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
    server, username, password, apikey, workspace, project = rallyWorkset(options)
    if apikey:
        rally = Rally(server, apikey=apikey, workspace=workspace, project=project)
    else:
        rally = Rally(server, user=username, password=password, workspace=workspace, project=project)
    rally.enableLogging("rally.hist.add_tcrs")

    if len(args) < 2:
        errout(USAGE)
        sys.exit(1)
    test_case_id, tcr_info_filename = args
    if not os.path.exists(tcr_info_filename):
        errout("ERROR:  file argument '%s' does not exist.  Respecify using corrent name or path\n" % tcr_info_filename)
        errout(USAGE)
        sys.exit(2)
    try:
        with open(tcr_info_filename, 'r') as tcif:
            content = tcif.readlines()
        tcr_info = []
        # each line must have Build, Date, Verdict
        for ix, line in enumerate(content):
            fields = line.split(',')
            if len(fields) != 3:
                raise Exception('Line #%d has invalid number of fields: %s' % (ix+1, repr(fields)))
            tcr_info.append([field.strip() for field in fields])
    except Exception:
        errout("ERROR: reading file '%s'.  Check the permissions or the content format for correctness." % tcr_info_filename)
        errout(USAGE)
        sys.exit(2)

    test_case = rally.get('TestCase', query="FormattedID = %s" % test_case_id,
                          workspace=workspace, project=None, instance=True)
    if not test_case or hasattr(test_case, 'resultCount'):
        print("Sorry, unable to find a TestCase with a FormattedID of %s in the %s workspace" % \
              (test_case_id, workspace))
        sys.exit(3)

    wksp = rally.getWorkspace()

    for build, run_date, verdict in tcr_info:
        tcr_data = { "Workspace" : wksp.ref,
                     "TestCase"  : test_case.ref,
                     "Build"     : build,
                     "Date"      : run_date,
                     "Verdict"   : verdict
                   }
        try:
            tcr = rally.create('TestCaseResult', tcr_data)
        except RallyRESTAPIError as details:
            sys.stderr.write('ERROR: %s \n' % details)
            sys.exit(4)
        
        print("Created  TestCaseResult OID: %s  TestCase: %s  Build: %s  Date: %s  Verdict: %s" % \
               (tcr.oid, test_case.FormattedID, tcr.Build, tcr.Date, tcr.Verdict))

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
