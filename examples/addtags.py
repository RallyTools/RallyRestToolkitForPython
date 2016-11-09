#!/usr/bin/env python
#################################################################################################
#
# addtags.py - example of how to add a collection to an item, in this case
#              adding some Tags to a Story.
#
USAGE = """\
Usage: python addtags.py <story_id> <tag_name> <tag_name> <tag_name>...
"""
#################################################################################################

import sys, os

from pyral import Rally, rallyWorkset, RallyRESTAPIError

#################################################################################################

errout = sys.stderr.write

VICTIM_TAG_NAME = 'Bad Food'

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, user, password, apikey, workspace, project = rallyWorkset(options)
    #rally = Rally(server, user, password, apikey=apikey, workspace=workspace)
    rally = Rally(server, user, password, workspace=workspace, project=project)
    rally.enableLogging("rally.history.addtags")

    if len(args) < 2:
        print(USAGE)
        sys.exit(1)

    story_id = args.pop(0)
    tag_names = args[:]
    tags = []

    story = rally.get('Story', fetch="FormattedID,Name,Description,Tags", 
                       query="FormattedID = %s" % story_id,
                       server_ping=False, isolated_workspace=True, instance=True)

    response = rally.get('Tag', fetch="true", order="Name", server_ping=False, isolated_workspace=True)
    for tag in response:
        print("Workspace %s  has tag: %-14.14s created on %s  Name: %s"  % \
              (tag.Workspace.Name, tag.oid, tag.CreationDate[:-5].replace('T', ' '), tag.Name))

        if tag.Name in tag_names:
            tags.append(tag)

    print("=====================================================")
    print(", ".join([tag.Name for tag in tags]))

    adds = rally.addCollectionItems(story, tags)
    print(adds)

    droppable_tags = [tag for tag in tags if tag.Name == VICTIM_TAG_NAME]
    print("dropping Tags %s ..." % ", ".join([tag.Name for tag in droppable_tags]))

    drops = rally.dropCollectionItems(story, droppable_tags)
    if drops.errors:
        print("Problem attempting to drop tags: %s" % drops.errors)
        sys.exit(2)

    story = rally.get('Story', fetch="FormattedID,Name,Description,Tags", 
                       query="FormattedID = %s" % story_id,
                       server_ping=False, isolated_workspace=True, instance=True)
    #print(story.details())
    print "story tags after deleting the '%s' Tag" % (droppable_tags[0].Name)

    story_tags = [str(tag.Name) for tag in story.Tags]
    print(story_tags)

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)

