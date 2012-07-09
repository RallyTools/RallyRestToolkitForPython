#!/usr/bin/env python

###################################################################################################
#
# wkspcounts - get per artifact type counts in a workspace (optionally broken out by project)
#
###################################################################################################

USAGE = """
Usage: python wkspcounts.py [-byproject] [art_type]
"""
###################################################################################################

import sys
import time

from pyral import rallySettings, Rally

###################################################################################################

errout = sys.stderr.write

COUNTABLE_ARTIFACT_TYPES = ['UserStory', 'Task', 'Defect', 
                            'TestCase', 'TestCaseResult',
                            'TestSet', 'TestFolder']

###################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, user, password, workspace, project = rallySettings(options)
    #print " ".join(["|%s|" % item for item in [server, user, '********', workspace, project]])
    rally = Rally(server, user, password, workspace=workspace, warn=False)
    rally.enableLogging('rally.hist.articount')  # name of file you want logging to go to
    prog_opts = [opt for opt in args if opt.startswith('-')]
    byproject = False
    if '-byproject' in prog_opts:
        byproject = True
    
    #if not args:
    #    errout(USAGE)
    #    sys.exit(1)

    print ""
    workspaces = rally.getWorkspaces()
    for wksp in workspaces:
        rally.setWorkspace(wksp.Name)
        print wksp.Name
        print "=" * len(wksp.Name)
        projects = [None]
        if byproject:
            projects = rally.getProjects(workspace=wksp.Name)
        for project in projects:
            if project:
                print ""
                print project.Name
                print "    %s" % ('-' * len(project.Name))
            for artifact_type in COUNTABLE_ARTIFACT_TYPES:
                count = getArtifactCount(rally, artifact_type, project=project)
                print "       %-16.16s : %4d items" % (artifact_type, count)
        print ""

###################################################################################################

def getArtifactCount(rally, artifact_type, project=None):
    if project:
        query='Project.Name = "%s"' % project.Name
        if artifact_type == 'TestCaseResult':
            query = 'TestCase.Project.Name = "%s"' % project.Name
        response = rally.get(artifact_type, fetch="FormattedID,Name",
                                            query=query,
                                            project=project.Name,
                                            projectScopeUp=False, projectScopeDown=False)
    else:
        response = rally.get(artifact_type, fetch="FormattedID,Name",
                                            project=None,
                                            projectScopeUp=False, projectScopeDown=False)
    if response.errors:
        print "Blarrggghhh! %s query error %s" % (artifact_type, response.errors[0])
        return 0

    return response.resultCount

###################################################################################################
###################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
