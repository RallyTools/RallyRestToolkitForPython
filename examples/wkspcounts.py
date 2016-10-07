#!/usr/bin/env python

###################################################################################################
#
# wkspcounts - get per artifact type counts in a workspace (optionally broken out by project)
#              note that only 'Open' Workspaces can be interrogated for artifact counts
#
###################################################################################################

USAGE = """
Usage: python wkspcounts.py {workspace | all} [-byproject] [art_type]
"""
###################################################################################################

import sys
import time

from pyral import Rally, rallyWorkset

###################################################################################################

errout = sys.stderr.write

COUNTABLE_ARTIFACT_TYPES = ['UserStory', 'Task', 'Defect', 
                            'TestCase', 'TestCaseResult',
                            'TestSet', 'TestFolder']

###################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, username, password, apikey, workspace, project = rallyWorkset(options)
    if apikey:
        rally = Rally(server, apikey=apikey, workspace=workspace, project=project)
    else:
        rally = Rally(server, user=username, password=password, workspace=workspace, project=project)
    
    target_workspace, byproject, art_types = processCommandLineArguments(args)
    rally.enableLogging('rally.hist.articount')  # name of file you want logging to go to
    
    workspaces = rally.getWorkspaces()
    if target_workspace != 'all':
        hits = [wksp for wksp in workspaces if wksp.Name == target_workspace]
        if not hits:
            problem = "The specified target workspace: '%s' either does not exist or is not accessible"
            errout("ERROR: %s\n" % (problem % target_workspace))
            sys.exit(2)
        workspaces = hits

    for wksp in workspaces:
        print(wksp.Name)
        print("=" * len(wksp.Name))
        rally.setWorkspace(wksp.Name)
        projects = [None]
        if byproject:
            projects = rally.getProjects(workspace=wksp.Name)
        for project in projects:
            if project:
                print("")
                print("    %s" % project.Name)
                print("    %s" % ('-' * len(project.Name)))
            for artifact_type in art_types:
                count = getArtifactCount(rally, artifact_type, project=project)
                print("       %-16.16s : %4d items" % (artifact_type, count))
        print("")

###################################################################################################

def processCommandLineArguments(args):
    workspaces = 'all'
    byproject  = False
    art_types  = COUNTABLE_ARTIFACT_TYPES

    prog_opts = [opt for opt in args if opt.startswith('-')]
    byproject = False
    if '-byproject' in prog_opts:
        byproject = True
        del args[args.index('-byproject')]

    if not args:
        errout(USAGE)
        sys.exit(1)

    workspaces = args.pop(0)  # valid is 'all' or the name of an Open workspace in the Subscription 

    if args:
        art_type = args[0]
        if art_type not in COUNTABLE_ARTIFACT_TYPES:
            errout("ERROR: The art_type given: '%s', is not in the list of valid artifact types below:\n")
            errout(", ".join(COUNTABLE_ARTIFACT_TYPES) + "\n")
            errout("\n")
            errout(USAGE)
            sys.exit(1)
        art_types = [art_type]

    return workspaces, byproject, art_types

###################################################################################################

def getArtifactCount(rally, artifact_type, project=None):
    if project:
        query = 'Project.Name = "%s"' % project.Name
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
        print("Blarrggghhh! %s query error %s" % (artifact_type, response.errors[0]))
        return 0

    return response.resultCount

###################################################################################################
###################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
