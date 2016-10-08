#!/usr/bin/env python

###################################################################################################
#
#  statecounts - for a given artifact_type within a workspace/project environment,
#                return the count of said artifact_type for each State/ScheduleState value.
#
USAGE = """
Usage: python statecounts.py <artifact_type>
"""
###################################################################################################

import sys
import time

from pyral import rallyWorkset, Rally

###################################################################################################

errout = sys.stderr.write

VALID_ARTIFACT_TYPES = ['Story', 'UserStory', 'HierarchicalRequirement', 'Defect', 'Task']

###################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, username, password, apikey, workspace, project = rallyWorkset(options)
    if apikey:
        rally = Rally(server, apikey=apikey, workspace=workspace, project=project)
    else:
        rally = Rally(server, user=username, password=password, workspace=workspace, project=project)

    rally.enableLogging('rally.hist.statecount')  # name of file you want logging to go to

    if not args:
        errout(USAGE)
        sys.exit(1)

    rally.setWorkspace(workspace)
    rally.setProject(project)

    artifact_type = args[0]
    if artifact_type not in VALID_ARTIFACT_TYPES:
        errout(USAGE)
        errout('The artifact_type argument must be one of: %s\n' % ", ".join(VALID_ARTIFACT_TYPES))
        sys.exit(1)
        
    art_type = artifact_type[:]
    state = 'State'  # default to this and change below if necessary
    if artifact_type in ['Story', 'UserStory', 'HierarchicalRequirement']:
        artifact_type = 'HierarchicalRequirement'
        state = 'ScheduleState'

    t_zero = time.time()
    state_values = rally.getAllowedValues(artifact_type, state)
    t_one = time.time()
    av_time = t_one - t_zero

    show_counts(rally, artifact_type, state, state_values, av_time)

###################################################################################################

def show_counts(rally, artifact_type, state, state_values, av_time):
    """
        Given a Rally connection instance, the name of the artifact type you want
        counts for, the name of the relevant state field (State or ScheduleState), 
        the valid state values for which counts will be obtained and an elapsed time
        value representing the time taken to retrieve the allowed values prior to this
        call, query for the counts for each state value and show the results.
    """
    output = []
   
    for state_value in sorted(state_values):
        response = rally.get(artifact_type, fetch="FormattedID", query='%s = %s' % (state, state_value),
                                            projectScopeUp=False, projectScopeDown=False)
        if response.errors:
            print("ERROR detected %s" % response.errors[0])
            sys.exit(1)
        output.append("%16s : %5d" % (state_value, response.resultCount))

    for line in output:
        print(line)

###################################################################################################
###################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
