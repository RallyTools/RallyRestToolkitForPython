#!/usr/bin/env python

#################################################################################################
#
#  crbug.py -- Create a Bug, populate the Abundanza multi-select field in the 'Jira 7 Testing'
#              workspace
#
USAGE = """
Usage: crbug.py 
"""
#################################################################################################

import sys, os
from pyral import Rally, rallyWorkset

#################################################################################################

errout = sys.stderr.write

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]

    server, user, password, apikey, workspace, project = rallyWorkset(options)
    if apikey:
        rally = Rally(server, apikey=apikey, workspace=workspace, project=project)
    else:
        rally = Rally(server, user=user, password=password, workspace=workspace, project=project)
#    rally.enableLogging("rally.history.crbug")

    target_project = rally.getProject()
    target_entity_name    = 'Defect'
    target_attribute_name = 'Abundanza'
    allowed_values = []
    candidate_values =  ['bosch', 'rybosome', 'stihl', 'snap-on']
    value_refs = []

    type_schema_attrs = rally.typedef(target_entity_name).Attributes
    ts_hits = [attr_schema for attr_schema in type_schema_attrs
                            if attr_schema.ElementName == f'c_{target_attribute_name}']
    if ts_hits:
        tsa = ts_hits[0]
        allowed_values = tsa.AllowedValues

    def notFound(target_value, allowed_values):
        hits = [aavs.value for aavs in allowed_values
                            if aavs.value == target_value]
        return True if not hits else False

    if allowed_values:
        disallowed_values = [cand_val for cand_val in candidate_values
                                       if notFound(cand_val, allowed_values)]
        if disallowed_values:
            for dav in disallowed_values:
                print(f'WARNING: {dav} is not an allowed value for the {target_entity_name}.{target_attribute_name} field')
            candidate_values = list(set(candidate_values) - set(disallowed_values))
        value_refs = getAllowedValueRefs(candidate_values, allowed_values)
    
    info = {
             "Project"        : target_project.ref,
             "Name"           : "Mushy fries sicken our customers",
             "State"          : "Submitted",
             "ScheduleState"  : "Defined",
             "Description"    : "revolt is soon to arrive at your franchise",
             "Notes"          : "I have really only done some daydreaming wrt this defect",
             #"Abundanza"      : "bosch,stihl,snap-on"
             "Abundanza"      : value_refs
           }

    print("Creating Defect ...")
    defect = rally.put('Defect', info)
    print("Created  Defect: %s   OID: %s" % (defect.FormattedID, defect.oid))
    #abund = defect.Abundanza
    abund = defect.c_Abundanza
    if abund:
        abund = ", ".join([aav.value for aav in abund])
    else:
        abund = ''

    print(f'         Abundanza: {abund}')
    #print(repr(defect.__dict__))
    #print(defect.details())

#################################################################################################

def getAllowedValueRefs(specified_values, allowed_values_schema):
    """
        Turn the specified values into refs to the corresponding
        allowedattributevalue items.
        have to return a structure like:
        [
          {'_ref' : 'allowedattributevalue/875421254' },
          {'_ref' : 'allowedattributevalue/875432439' },
          ...
        ]
    """
    ref_box = []
    for aav_text in specified_values:
        hits = [aavs.ref for aavs in allowed_values_schema
                         if aavs.value == aav_text]
        if hits:
            ref = hits[0]
            ref_box.append({'_ref' : ref})
    return ref_box

#################################################################################################


def emptyDefect():
    task = {'Workspace'      : '',
            'Project'        : '',
            'Name'           : '', 
            'State'          : '',
            'ScheduleState'  : '',
           }
    return task

#################################################################################################

def queryForDefects(rally):
    response = rally.get('Defect', fetch=True)
    # a response has status_code, content and data attributes

    for defect in response:
        #print "%s  %s  %s  %s" % (defect.__class__.__name__, defect.oid, defect.name, defect._ref)
        print("%s  %s  %s  %s  %s  %s" % (defect.FormattedID,    defect.Name, 
                                          defect.Workspace.Name, defect.Project.Name,
                                          defect.Release.Name,   defect.Iteration.Name))

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
