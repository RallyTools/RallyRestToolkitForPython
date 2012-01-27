#!/usr/bin/env python

#################################################################################################
#
#  crtask.py -- Create a Task, have it associated with specific UserStory
#
USAGE = """
Usage: crtask.py <Story FormattedID>
"""
#################################################################################################

import sys, os
from pyral import Rally, rallySettings

#################################################################################################

errout = sys.stderr.write

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    if len(args) != 1:
        errout(USAGE)
        sys.exit(1)
    storyID = args[0]

    server, user, password, workspace, project = rallySettings(options)
    rally = Rally(server, user, password, workspace=workspace, project=project)
    rally.enableLogging("rally.history.crtask")

    # For a task: Workspace, Project, WorkProduct, Name, State, TaskIndex are required;
    # Workspace cannot be specified in the JSON, it defaults to 
    # the logged in account's Workspace setting
    # Project and WorkProduct must be object refs to relevant Rally Entity instances.
    # In this example the WorkProduct is a UserStory (HierarchicalRequirement).

    target_project = rally.getProject()
    target_story   = rally.get('UserStory', query='FormattedID = %s' % storyID, instance=True)
    
    info = {
             "Project"     : target_project.ref,
             "WorkProduct" : target_story.ref,
             "Name"        : "BigTaters",
             "State"       : "Defined",
             "TaskIndex"   : 1,
             "Description" : "Fly to Chile next week to investigate the home of potatoes.  Find the absolute gigantoidist spuds and bring home the eyes to Idaho.  Plant, water, wonder, harvest, wash, slice, plunge in and out of hot oil, drain and enjoy! Repeat as needed.",
             "Estimate"    : 62.0,
             "Actuals"     :  1.0,
             "ToDo"        : 61.0,
             "Notes"       : "I have really only done some daydreaming wrt this task.  Sorry Jane, I knew you had big plans for Frankie's blowout BBQ next month, but the honeycomb harvest project is taking all my time."
           }

    print "Creating Task ..."
    task = rally.put('Task', info)
    print "Created  Task: %s   OID: %s" % (task.FormattedID, task.oid)

#################################################################################################

def emptyTask():
    task = {'Workspace'   : '',
            'Project'     : '',
            'Name'        : '', 
            'Owner'       : '',
            'Description' : '',
            'Release'     : '',
            'Iteration'   : '',
            'WorkProduct' : '',
            'Estimate'    : '',
            'Actuals'     : '',
            'TaskIndex'   : '',
            'Text'        : '',
            'Notes'       : '',
            'Rank'        : '',
            'State'       : '',
            'ToDo'        : '',
            'Blocked'     : '',
            'Tags'        : '',
           }
    return task

#################################################################################################

def queryForTasks(rally):
    response = rally.get('Task', fetch=True)
    # a response has status_code, content and data attributes

    for task in response:
        #print "%s  %s  %s  %s" % (task.__class__.__name__, task.oid, task.name, task._ref)
        print "%s  %s  %s  %s  %s  %s" % (task.FormattedID,    task.Name, 
                                          task.Workspace.Name, task.Project.Name,
                                          task.Release.Name,   task.Iteration.Name)

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
