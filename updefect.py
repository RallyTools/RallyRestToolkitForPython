#!/usr/bin/env python
#################################################################################################
#
# updefect.py - example of how to effect an update to an existing Defect
#                specifically changing the Project for the Defect
#
USAGE = """\
Usage: python updefect.py <DefectID> <attribute> <value>
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
    #workspace = 'Alligators WRK Smoke JIRA'
    #project   = 'JIRA 7.x'
    workspace = 'JIRA 7 Testing'
    project   = 'Sample Project'
    rally = Rally(server, user, password, apikey=apikey, workspace=workspace, project=project)
    #rally.enableLogging("rally.history.updefect")

    #args = ['DE21209', 'Description']
    links_block = """\
    <p><a href="https://chooki.com/img/food_2.jpg">[https://chooki.com/img/food_2.jpg</a>]</p><br />
    <p><a href="https://chooki.com/img/food_2.jpg">finiky ediblus</a></p><br />
    <p><a href="https://chooki.com/img/food_2.jpg">glorious CKEditor food pic</a></p><br />
    <p><a href="https://chooki.com/img/food_2.jpg">small image of food plate</a></p><br />
"""
    #args.append(links_block)

    if len(args) != 3:
        print(USAGE)
        sys.exit(1)

    defect_id, attribute, value = args[:3]
    value = """
<p><span style="color:#4c9aff;">Huubina treandle korz</span></p>
<p>&nbsp;</p> 
<p><i>Links</i><br>Link to giphy <a href="https://giphy.com|smart-link">https://giphy.com</a></p>
<p>&nbsp;</p> <p>on to 
<a href="http://www.windy.com|smart-link">http://www.windy.com</a></p>
<p>&nbsp;</p> 
<p><i>Images</i><br>Uploaded</p>
<hr> 
<figure class="image image_resized" style="width:80%">
<img src="/slm/attachment/730942835535/moab-winter-dusting.jpg">
</figure>
<hr>
<p>&nbsp;</p> 
<h3>Just some verbal spillage for testing</h3>
<p>&nbsp;</p> 
<p>Merlin <s>commanded</s> advised me to tell you to give-me-a-break 
whenever i tell you to <s>stfu</s> put a brick in your <s>piehole</s> mouth, 
go-to-he-double-hockey-sticks doofus and <s>donty never sully my palace again</s>!</p>
<p>&nbsp;</p> <p>Linked<br>
<a href="https://food.com/latest/assets/img/food_2.jpg">https://food.com/latestassets/img/food_2.jpg</a>
</p>
<p>&nbsp;</p> <p><img src="alta-harbor.jpg" alt="alta-harbor.jpg"></p>
<p>&nbsp;</p> <p>Isn’t Alta harbor cold and beautiful?</p>
<p>&nbsp;</p> <p>Can’t anybody figure out how to get a table to be obtuse to the max?</p>
<p>&nbsp;</p> 
<figure class="table"><table>
<thead><tr><th><strong>manufacturer</strong></th><th><strong>year</strong></th><th><strong>country</strong></th></tr></thead>
    <tbody>
        <tr><td>mercedes</td><td>1965</td><td>germany</td></tr>
        <tr><td>toyota</td><td>2003</td><td>japan</td></tr>
        <tr><td>fored</td><td>2010</td><td>usa</td></tr>
    </tbody>
</table></figure>
<p>&nbsp;</p>
<p>never let me down…</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<figure class="image">
<img src="/slm/attachment/730939835245/alta-harbor.jpg">
</figure>
    """
    target_oid = None

    response = rally.get('Defect', fetch="ObjectID,Name,FormattedID,Project,Description,Tags",
                                   query=f"FormattedID = {defect_id}", isolated_workspace=True)
    defect = response.next()
    #print(f'target Defect OID value: {defect.oid}')
    #print(f'current Project value is {defect.Project.Name}')
    print(f"FormattedID: {defect.FormattedID}  ObjectID: {defect.oid}  Name: {defect.Name} Description:\n{defect.Description}\n-----------------\n")
    #sys.exit(0)

    #dest_project = rally.getProject(name=value)
    #print(f'Project "{dest_project.Name}" OID: {dest_project.oid}   ref: {dest_project.ref}')

#    for tag in response:
#        print("Workspace %s  has tag: %-14.14s created on %s  Name: %s"  % \
#              (tag.Workspace.Name, tag.oid, tag.CreationDate[:-5].replace('T', ' '), tag.Name))
#        if tag.Name == target_name:
#            target_oid = tag.oid
#
#    if not target_oid:
#        print("No Tag exists with a Name value of |%s|" % target_name)
#        sys.exit(1)
#
    #upd_info = {"FormattedID" : defect_id, "Project" : dest_project.ref }
    #print(upd_info)

    #upd_info = {'FormattedID' : defect_id, 'Description' : links_block}

    upd_info = {"FormattedID" : defect_id, "Description" : value}

    try:
        defect = rally.update('Defect', upd_info)
    except RallyRESTAPIError as exc:
        sys.stderr.write(f'ERROR: {str(exc)}')
        sys.exit(2)

    print("Defect updated")
    #print(f'FormattedID: {defect.FormattedID}  ObjectID: {defect.oid}  Name: {defect.Name}  Project: {defect.Project.Name}')
    print(f"FormattedID: {defect.FormattedID}  ObjectID: {defect.oid}  Name: {defect.Name} Description:\n{defect.Description}\n-----------------\n")

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)

