#!/usr/bin/env python

###################################################################################################
#
# wkspcounts - get per artifact type counts in a workspace (optionally broken out by project)
#              note that only 'Open' Workspaces can be interrogated for artifact counts
#
###################################################################################################

USAGE = """
Usage: python wkspcounts.py {workspace | all} [-byproject] [art_type]

       if art_type not specified all common artifact types are included
"""
###################################################################################################

import sys
import time

from pyral import Rally, rallyWorkset

###################################################################################################

errout = sys.stderr.write

COUNTABLE_ARTIFACT_TYPES = ['Feature','UserStory', 'Task', 'Defect', 
                            'TestCase', 'TestCaseResult',
                            'TestSet', 'TestFolder']

###################################################################################################

def main(args):
    original_args = args[:]
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    wksp_arg = args.pop(0)
    
    server, username, password, apikey, workspace, project = rallyWorkset(options)
    if wksp_arg == 'all':
        if apikey:
            rally = Rally(server, apikey=apikey, workspace=workspace, project=project)
        else:
            rally = Rally(server, user=username, password=password, 
                          workspace=workspace, project=project)
    else:
        if apikey:
            rally = Rally(server, apikey=apikey, workspace=wksp_arg, project=project, 
                          isolated_workspace=True)
        else:
            rally = Rally(server, user=username, password=password, 
                          workspace=wksp_arg, project=project, isolated_workspace=True)

    byproject, art_types = processCommandLineArguments(args)

    wksp = rally.getWorkspace()
    workspaces = rally.getWorkspaces()
    if wksp_arg != 'all':
        hits = [wksp for wksp in workspaces if wksp.Name == target_workspace]
        if not hits:
            problem = "The specified target workspace: '%s' either does not exist or is not accessible"
            errout("ERROR: %s\n" % (problem % target_workspace))
            sys.exit(2)
        workspaces = hits

    for wksp in workspaces:
        rally.setWorkspace(workspace.Name)
        print(wksp.Name)
        print("=" * len(wksp.Name))

        showArtifactCounts(rally, wksp, byproject)

###################################################################################################

def showArtifactCounts(rally, workspace, byproject):
    if byproject:
        projects = rally.getProjects(workspace=wksp.Name)
        for project in projects:
            if project:
                 print("")
                 print(f"    {project.Name}" % project.Name)
                 dashes = '-' * len(project.Name)
                 print(f"    {dashes}")
            for artifact_type in art_types:
                count = getArtifactCount(rally, artifact_type, project=project)
                print("       {artifact_type:>16} : {count:4d} items")
    else:
        for artifact_type in art_types:
            count = getArtifactCount(rally, artifact_type, project=None)
            print("       {artifact_type:>16} : {count:4d} items")

    print("")

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

def processCommandLineArguments(args):
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

    art_type = args.pop()
    if art_type not in COUNTABLE_ARTIFACT_TYPES:
        problem = f'The art_type given: '{art_type}', is not in the list of valid artifact types below:'
        errout(f"ERROR: {problem}\n")
        errout(", ".join(COUNTABLE_ARTIFACT_TYPES) + "\n")
        errout("\n")
        errout(USAGE)
        sys.exit(1)
    art_types = [art_type]

    return byproject, art_types

###################################################################################################
###################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
