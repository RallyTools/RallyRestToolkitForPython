#!/usr/bin/env python

#################################################################################################
#
#  uptask.py -- Update a Task identified by the FormattedID value
#
USAGE = """
Usage: uptask.py <Task FormattedID>
"""
#################################################################################################

import sys, os

from pyral import Rally, RallyRESTAPIError, rallySettings

#################################################################################################

errout = sys.stderr.write

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    if len(args) != 1:
        errout(USAGE)
        sys.exit(1)

    server, user, password, workspace, project = rallySettings(options)
    rally = Rally(server, user, password, workspace=workspace, project=project)
    rally.enableLogging("rally.history.uptask")

    taskID = args.pop()   # for this example use the FormattedID
    print "attempting to update Task: %s" % taskID

    #
    # following assumes there is:
    #     a User in the system whose DisplayName is 'Crandall',
    #     a UserStory with a FormattedID of S12345, 
    #     a Release with a name of 'April-A', 
    #    an Iteration with a Name of 'Ivanhoe' 
    # within the current Workspace and Project.
    #
    owner_name = 'Crandall'
    storyID    = 'S12345'
    release_target  = 'April-A'
    iteration_targe = 'Ivanhoe'

    target_workspace = rally.getWorkspace()
    target_project   = rally.getProject()
    target_owner = rally.getUserInfo(name=owner_name).pop(0) # assume a unique match...

    release      = rally.get('Release',   query='Name = %s' % release_target,   instance=True)
    iteration    = rally.get('Iteration', query='Name = %s' % iteration_target, instance=True)
    target_story = rally.get('UserStory', query='FormattedID = %s' % storyID,   instance=True)

    info = {
             "Workspace"     : target_workspace.ref,
             "Project"       : target_project.ref,
             "FormattedID"   : taskID,
             "Name"          : "Stamp logo watermark on all chapter header images",
             "Owner"         : target_owner.ref,
             "Release"       : release.ref,
             "Iteration"     : iteration.ref,
             "WorkProduct"   : target_story.ref,
             "State"         : "Completed",
             "Rank"          : 2,
             "TaskIndex"     : 2,
             "Estimate"      : 18.0,
             "Actuals"       : 2.5,
             "ToDo"          : 15.5,
             "Notes"         : "Bypass any GIFs, they are past end of life date",
             "Blocked"       : "false"
           }

##    print info   

    try:
        task = rally.update('Task', info)
    except RallyRESTAPIError, details:
        sys.stderr.write('ERROR: %s \n' % details)
        sys.exit(2)

    print "Task updated" 
    print "ObjectID: %s  FormattedID: %s" % (task.oid, task.FormattedID)

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])

