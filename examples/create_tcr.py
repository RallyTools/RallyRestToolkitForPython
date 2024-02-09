#!/usr/bin/env python

#################################################################################################
#
#  create_tcr.py -- Add TestCaseResult with relevant info AND links (refs) to a TestCase and TestSet
#
USAGE = """
Usage: create_tcr.py <TestCase short_ref> <TestSet short_ref>
"""
#################################################################################################

import sys, os
from pprint import pprint
from pyral import Rally, rallyWorkset, restapi
RallyRESTAPIError = restapi.RallyRESTAPIError

#################################################################################################

errout = sys.stderr.write

WORKSPACE = "/workspace/56371159504"   # HPALM
PROJECT   = "/project/56371159588"     # Test Project

TEST_CASE_REF = "/testcase/437141174052"
TEST_SET_REF  = "/testset/436906646904"

#TEST_CASE_REF = "/testcase/436896580816"
#TEST_SET_REF  = "/testset/436906646904"

build    = "1847"
run_date = "2020-09-22T16:23:20.000Z"
verdict  = "Pass"

zhpalm_run = {"Workspace" : "/workspace/56371159504",   # HPALM
             "Project"   : "/project/56371159588",     # Test Project
             "TestCase"  : "/testcase/436896580816",   # lush green vistas
             "TestSet"   : "/testset/436906646904",    # HP12 complex test 3 rally test set HP release cycle
             "Build"     : "3917", 
             "Date"      : "2020-09-21T23:03:20.000Z", 
             "Verdict"   : "Fail", 
            }


hpalm_run = {
            #"Workspace" : "/workspace/56371159504", 
            "Workspace" : "https://rally1.rallydev.com/slm/webservice/v2.0/workspace/56371159504",
            "Project"   : "/project/56371159588",
            "TestCase"  : "/testcase/61078205410", 
            "TestSet"   : "/testset/436906631556", 
            "Build"     : "load linked run #1", 
            "Date"      : "2020-09-03T21:50:48.000Z", 
            "Verdict"   : "Fail", 
            "Duration"  : "0", 
            "Tester"    : "https://rally1.rallydev.com/slm/webservice/v2.0/user/56374751020"
            }

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
    #rally.enableLogging("rally.hist.add_tcrs")

    #if len(args) < 2:
    #    errout(USAGE)
    #    sys.exit(1)
    #test_case_ref, test_set_ref = args

    tcr_data = { "Workspace" : WORKSPACE,
                 "Project"   : PROJECT,
                 "TestCase"  : TEST_CASE_REF,
                 "TestSet"   : TEST_SET_REF,
                 "Build"     : build,
                 "Date"      : run_date,
                 "Verdict"   : verdict
               }
    #pprint(tcr_data)
    #try:
    #    tcr = rally.create('TestCaseResult', tcr_data)
    #except RallyRESTAPIError as details:
    #    sys.stderr.write('ERROR: %s \n' % details)
    #    sys.exit(4)

    pprint(hpalm_run)
    try:
        tcr = rally.create('TestCaseResult', hpalm_run)
    except RallyRESTAPIError as details:
        sys.stderr.write('ERROR: %s \n' % details)
        sys.exit(4)
    
    
    #print(tcr.details())
    print("")
    print("Created  TestCaseResult OID: %s  TestCase: %s  TestSet: %s" %
           (tcr.oid, tcr.TestCase.ref, tcr.TestSet.ref))
    print("    Build: %s  Date: %s  Verdict: %s" % (tcr.Build, tcr.Date, tcr.Verdict))

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])

