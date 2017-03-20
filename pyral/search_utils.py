__version__ = (1, 2, 4)

from operator import attrgetter

import six

def projectAncestors(target_project, project_pool, ancestors):
    if target_project.Parent:
        ancestors.append(target_project.Parent)
        projectAncestors(target_project.Parent, project_pool, ancestors)
    return reversed(ancestors)

def projeny(target_project, project_pool, lineage, level):
    """
        Given a target Project instance (with oid, ref and Name) populate
        a dict with the hierachical list of child projects in a recursive
        fashion.
    """
    lineage[target_project] = {}
    child_projects = [proj for proj in project_pool 
                            if proj.Parent 
                           and proj.Parent.ref == target_project.ref
                     ]
    for child in child_projects:
        projeny(child, project_pool, lineage[target_project], level+1)

def flatten(target_dict, sort_attr, list_o_things):
    """
        Given a dict (whose structure is a hierarcy), arrange all
        keys to be in a flat list of values.
        
    """
    for key in sorted(list(target_dict.keys()), key=attrgetter(sort_attr)):
        list_o_things.append(getattr(key, sort_attr))
        value = target_dict[key]
        if isinstance(value, dict):
            flatten(value, sort_attr, list_o_things)
    return list_o_things

def projectDescendants(target_project, project_pool):
    #descendents = {target_project : {}}
    descendents = {}
    projeny(target_project, project_pool, descendents, 1)
    return flatten(descendents, 'Name', [])

class MockRallyRESTResponse(object):
    """
        An instance of this class is used by the Rally search method to 
        wrap any filtered results into an object that superficially behaves
        like a RallyRESTResponse instance
    """
    def __init__(self, items):
        self.items = iter(items)
        self.resultCount = len(items)
        self._item_type = 'SearchObject'
        self.status_code = 200
        self.errors      = []
        self.warnings    = []

    def __iter__(self):
        return self.items

    def __next__(self):
        return six.next(self.items)

