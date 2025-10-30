#!/usr/bin/env python

#################################################################################################
#
#  get_repositories.py - show all the Repositories in the target Workspace
#
USAGE = """
Usage: python repositories.py  {workspace_name}
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
    workspace = args.pop(0) if args else workspace

    if apikey:
        rally = Rally(server, apikey=apikey, workspace=workspace,
                      project=project, isolated_workspace=True)
    else:
        rally = Rally(server, user=username, password=password, workspace=workspace,
                      project=project, isolated_workspace=True)

    showRepositories(rally, workspace=workspace, limit=ITEM_LIMIT)

#################################################################################################

def showRepositories(rally, workspace=None, limit=200):
    
    try:
        response = rally.get('SCMRepository', fetch=True,
                             order="CreationDate ASC",
                             workspace=workspace, project=None,
                             pagesize=1000, limit=limit)
    except Exception as msg:
        print(msg)
        return None

    if response.errors:
        errout("SCMRepository request could not be successfully serviced, error code: %d\n" % \
               response.status_code)
        return None

    for repo in response:
        print(f'{repo.oid}  {repo.Name:<24.24}  {repo.SCMType:<10.10}   {repo.CreationDate}')

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
