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

        value = """
<p><span style="color:#4c9aff;">Huubina treandle korz</span></p>
<p>&nbsp;</p> <p><i>Links</i><br>Link to giphy <a href="https://giphy.com|smart-link">https://giphy.com</a></p>
<p>&nbsp;</p> <p>on to <a href="http://www.windy.com|smart-link">http://www.windy.com</a></p>
<p>&nbsp;</p> <p><i>Images</i><br>Uploaded</p>
<hr> 
<figure class="image image_resized" style="width:80%"><img src="/slm/attachment/730942835535/moab-winter-dusting.jpg"></figure>
<hr>
<p>&nbsp;</p> <p><img src="bff5de03-823d-41ab-a448-3be70f94ec23#media-blob-url=true&amp;id=cb54963b-2da1-4cf6-8642-1a2d7c815ab4&amp;collection=upload-user-collection-92668751&amp;contextId=12489&amp;width=226&amp;height=144&amp;alt=|width=777,height=496" alt="bff5de03-823d-41ab-a448-3be70f94ec23"></p>
<p>&nbsp;</p> <h3>Just some verbal spillage for testing</h3><p>&nbsp;</p> <p>Merlin <s>commanded</s> advised me to tell you to give-me-a-break whenever i tell you to <s>stfu</s> put a brick in your <s>piehole</s> mouth, go-to-he-double-hockey-sticks doofus and <s>donty never sully my palace again</s>!</p>
<p>&nbsp;</p> <p>Linked<br><a href="https://ckeditor.com/docs/ckeditor5/latest/assets/img/food_2.jpg">https://ckeditor.com/docs/ckeditor5/latest/assets/img/food_2.jpg</a></p>
<p>&nbsp;</p> <p><img src="alta-harbor.jpg|width=57600,height=43200" alt="alta-harbor.jpg"></p>
<p>&nbsp;</p> <p>Isn’t Alta harbor cold and beautiful?</p>
<p>&nbsp;</p> <p>Can’t anybody figure out how to get a table to be obtuse to the max?</p>
<p>&nbsp;</p> <figure class="table"><table><thead><tr><th><strong>manufacturer</strong></th><th><strong>year</strong></th><th><strong>country</strong></th></tr></thead><tbody><tr><td>mercedes</td><td>1965</td><td>germany</td></tr><tr><td>toyota</td><td>2003</td><td>japan</td></tr><tr><td>fored</td><td>2010</td><td>usa</td></tr></tbody></table></figure><p>&nbsp;</p> <p>|_.*Too Tall to think*|<br>F</p>
<p>&nbsp;</p> <p>&lt;figure class="image"&gt;&lt;img src="/slm/attachment/730939833657/inxs-devil-inside.jpg"&gt;&lt;/figure&gt;</p>
<p>&nbsp;</p> <p>never let me down…</p>
<p>&nbsp;</p> <p>&nbsp;</p> <figure class="image"><img src="/slm/attachment/730939835245/alta-harbor.jpg"></figure>
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

