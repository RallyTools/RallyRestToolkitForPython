#!/usr/bin/env python

#################################################################################################
#
# delete_repo.py -- Delete a named SCMRepository
#
USAGE = """
Usage: delete_repo.py {workspace_name} <repo_name>
"""
#################################################################################################

import sys
import re
import string

from pyral import Rally, rallyWorkset

#################################################################################################

errout = sys.stderr.write

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]

    server, username, password, apikey, workspace, project = rallyWorkset(options)

    if not args:
        print(f'No SCMRepository name was given.  You must provide the name of a SCMRepository')
        sys.exit(1)
    if args == 2:
        workspace = args.pop(0)
    repo_name = args.pop()

    if apikey:
        rally = Rally(server, apikey=apikey,   workspace=workspace,
                              project=project, isolated_workspace=True)
    else:
        rally = Rally(server, user=username, password=password, workspace=workspace,
                                             project=project,   isolated_workspace=True)

    response = rally.get('SCMRepository', fetch="ObjectID,Name,SCMType,CreationDate,LastUpdate",
                         query=f'Name = "{repo_name}"',
                         workspace=workspace,
                         order="ObjectID DESC", limit=10)

    print(f'query resultCount: {response.resultCount}')
    if response.resultCount == 0:
        print(f'No SCMRepository with the name of "{repo_name}" exists, no deletion attempted.')
        return None
    elif response.resultCount > 1:
        print(f'Multiple SCMRepository items with the name of "{repo_name}" exist, no deletion attempted.')
        for repo in response:
            print(f'{repo.oid} {repo.Name} {repo.SCMType} {repo.CreationDate}')
        return None

    victim = response.next()
    result = rally.delete('SCMRepository', victim.oid)
    print(f"SCMRepository record for '{repo_name}' was deleted? {result}")

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
