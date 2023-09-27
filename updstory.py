#!/usr/bin/env python
#################################################################################################
#
# upstory.py - example of how to effect an update to an existing Story
#                specifically changing the Description to include the
#                CKEditor markup for links
#
USAGE = """\
Usage: python updstory.py <StoryID> <attribute> <value>
"""
#################################################################################################

import sys, os

from pyral import Rally, rallyWorkset, RallyRESTAPIError

#################################################################################################

errout = sys.stderr.write

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, user, password, apikey, workspace, project = rallyWorkset(options)
    workspace = 'Yeti Rally Workspace'
    project   = 'Danish Cookies'
    rally = Rally(server, user, password, apikey=apikey,
                  workspace=workspace, project=project,
                  isolated_workspace=True)
    #rally.enableLogging("rally.history.updstory")

    if not args:
        print(USAGE)
        sys.exit(1)

    if len(args) == 3:
        story_id , attribute, value = args[:3]
    else:
        story_id = args[0]
        attribute = 'Description'
        value = """
<p><a href="https://ckeditor.com/docs/ckeditor5/latest/assets/img/food_2.jpg">[https://ckeditor.com/docs/ckeditor5/latest/assets/img/food_2.jpg]</a></p>
<p><a href="https://ckeditor.com/docs/ckeditor5/latest/assess/img/food_2.jpg">finiky ediblus</a></p>
<p><a href="https://ckeditor.com/docs/ckeditor5/latest/assets/img/food_2.jpg">glorious CKEditor food pic</a></p>
<p><a href="https://ckeditor.com/docs/ckeditor5/latest/assets/img/food_2.jpg">small image of food plate</a></p>

<p>&nbsp;</p>

<p><a href="https://ckeditor.com/docs/ckeditor5/latest/assets/img/food_2.jpg">https://ckeditor.com/docs/ckeditor5/latest/assets/img/food_2.jpg</a></p>
<p>&nbsp;</p>
<p>[funky chicken|<a href="https://ckeditor.com/docs/ckeditor5/latest/assets/img/food_2.jpg">assets</a>]</p>
<p>&nbsp;</p>
<p>regular text</p
><p>&nbsp;</p>
<p>[<a href="https://ckeditor.com/docs/ckeditor5/latest/assets/img/food_2.jpg">jones boys|https://ckeditor.com/docs/ckeditor5/latest/assets/img/food_2.jpg</a>]</p>
<p>&nbsp;</p>
<p><a href="https://ckeditor.com/docs/ckeditor5/latest/assets/img/food_2.jpg">hibeam</a></p>

<p>&nbsp;</p>
"""
    target_oid = None
    response = rally.get('Story', fetch="ObjectID,Name,FormattedID,Project,Description,Tags",
                                   query=f"FormattedID = {story_id}", isolated_workspace=True)
    story = response.next()
    print(f'target Story OID value: {story.oid}')

    upd_info = {"FormattedID" : story_id,
                attribute     : value,
               }
    print(upd_info)
    
    try:
        story = rally.update('Story', upd_info)
    except RallyRESTAPIError as exc:
        sys.stderr.write(f'ERROR: {str(exc)}')
        sys.exit(2)

    print("Story updated")
    print(f'FormattedID: {story.FormattedID}  ObjectID: {story.oid}  Name: {story.Name}  Project: {story.Project.Name}')

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)

