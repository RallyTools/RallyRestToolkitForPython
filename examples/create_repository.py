#!/usr/bin/env python

#################################################################################################
#
#  create_repository.py - create a SCMRepository item in the target Workspace
#
USAGE = """
Usage: python create_repository.py {workspace_name} <repository_name> <repo_type>
"""
#################################################################################################

import sys, os
import time

from pyral import Rally, rallyWorkset

#################################################################################################

ITEM_LIMIT = 1000

errout = sys.stderr.write

oid_cache = {}

#################################################################################################

def main(args):

    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]

    server, username, password, apikey, workspace, project = rallyWorkset(options)
    if len(args) < 2 or len(args) > 3:
        print(USAGE)
        sys.exit(1)
    if len(args) == 3:
        workspace, repo_name, repo_type = args[:]
    elif len(args) == 2:
        repo_name, repo_type = args[:]
        if repo_type.lower() not in ["cvs", 'svn', 'git', 'github', 'gitlab', 'bitbucket']:
            print(f"repo_type argument: {repo_type} not recognized as a plausible repo_type value ")
            sys.exit(2)

    if apikey:
        rally = Rally(server, apikey=apikey, workspace=workspace, project=project,
                                             isolated_workspace=True)
    else:
        rally = Rally(server, user=username, password=password, workspace=workspace,
                                             project=project,   isolated_workspace=True)

    createRepository(rally, workspace, repo_name, repo_type)

#################################################################################################

def createRepository(rally, workspace, repo_name, repo_type):

    spec = {"Name"    : repo_name,
            "SCMType" : repo_type
           }

    try:
        scm_repo = rally.create('SCMRepository', spec, workspace=workspace, project=None)
    except Exception as msg:
        print(msg)
        return None
    print(f'{scm_repo.oid}  {scm_repo.Name:<24.24}  {scm_repo.SCMType:<10.10}   {scm_repo.CreationDate}')


#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
