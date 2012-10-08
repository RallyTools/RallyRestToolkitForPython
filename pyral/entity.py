
###################################################################################################
#
#  pyral.entity - defines the entities in Rally, exposes a classFor dict
#                 to allow instantiation of concrete Rally entities
#          dependencies:
#               intra-package: the getResourceByOID and hydrateAnInstance functions from restapi
#
###################################################################################################

__version__ = (0, 9, 3)

import sys
import re

from .restapi   import hydrateAnInstance
from .restapi   import getResourceByOID

##################################################################################################

VERSION_ATTRIBUTES = ['_rallyAPIMajor', '_rallyAPIMinor', '_objectVersion']
MINIMAL_ATTRIBUTES = ['_type', '_ref', '_refObjectName']

_rally_entity_cache = {}
_typedefs_slurped     = False

##################################################################################################

class UnreferenceableOIDError(Exception): 
    """
        An Exception to be raised in the case where an Entity/OID pair in a _ref field
        cannot be retrieved.
    """
    pass

class InvalidRallyTypeNameError(Exception):
    """
        An Exception to be raised in the case where a candidate Rally entity name
        doesn't resolve to a valud Rally entity.
    """
    pass

##################################################################################################
#
# Classes for each entity in the Rally data model.  Refer to the Rally REST API document
# for information on the Rally data model.  You'll note that in the data model there are
# the equivalent of abstract classes and that the code here doesn't strictly enforce that.
# However, the instantiation of any Rally related classes takes place through the classFor
# mechanism which only enables instances of a concrete class to be provided.
#
class Persistable(object):  
    def __init__(self, oid, name, resource_url, context):
        """
            All sub-classes have an oid (Object ID), so it makes sense to provide the 
            attribute storage here.
        """
        self.oid = oid
        self.Name = name
        self._ref = resource_url
        self._hydrated = False
        self._context = context

    def attributes(self):
        """
            return back the attributes of this instance minus the _context 
        """
        attrs = sorted(self.__dict__.keys())
        attrs.remove('_context')
        return attrs

    def __getattr__(self, name):
        """
           This is needed to implement the first swag of lazy attribute evaluation.
           It only gets called if attribute lookup for the name has resulted in the "no-joy" situation.  
           Example: someone has an instance of a Project class.  
           They refer to p.Children[7].Owner.UserProfile.DefaultWorkspace.State
           Example 2: someone has an instance of a UserStory class that isn't fully hydrated 
           They refer to s.Iterations or s.FormattedID (both of which weren't in the 
           original fetch spec)
        """
        rallyEntityTypeName = self.__class__.__name__
        faultTrigger = "getattr fault detected on %s instance for attribute: %s  (hydrated? %s)" % \
                       (rallyEntityTypeName, name, self._hydrated)
##
##        print faultTrigger
##        sys.stdout.flush()
##
        if name == 'context':
            raise Exception('CRAP!  __getattr__ called for context attribute')
        if not self._hydrated:
            #
            # get "hydrated" by issuing a GET request for the resource referenced in self._ref
            # and having an EntityHydrator fill out the attributes, !!* on this instance *!!
            #
            entity, oid = self._ref.split('/')[-2:]
##
##            print "issuing OID specific get for %s OID: %s (from %s OID: %s)..." % \
##                  (entity, oid, rallyEntityTypeName, self.oid)
##            print "Entity: %s context: %s" % (rallyEntityTypeName, self._context) 
##            sys.stdout.flush()
##
            response = getResourceByOID(self._context, entity, self.oid, unwrap=True)
##
##            print "response is a %s" % type(response)
##            sys.stdout.flush()
##
            if not response:
                raise UnreferenceableOIDError("%s OID %s" % (rallyEntityTypeName, self.oid))
            if not isinstance(response, object): # TODO: would like to be specific with RallyRESTResponse here...
                print "bad guess on response type in __getattr__, response is a %s" % type(response)
                raise UnreferenceableOIDError("%s OID %s" % (rallyEntityTypeName, self.oid))
            if response.status_code != 200:
                raise UnreferenceableOIDError("%s OID %s" % (rallyEntityTypeName, self.oid))
            item = response.content[rallyEntityTypeName]
##
##            print "calling hydrateAnInstance from the __getattr__ of %s for %s" % (name, self._type)
##            sys.stdout.flush()
##
            hydrateAnInstance(self._context, item, existingInstance=self)
            self._hydrated = True

        if name in self.attributes():
            return self.__dict__[name]
        elif name == "ref":
            entity_name, oid = self._ref.split('/')[-2:]
            return '%s/%s' % (entity_name, oid.replace('.js', ''))
        else:    
            description = "%s instance has no attribute: '%s'" % (rallyEntityTypeName, name)
            raise AttributeError(description)

##################################################################################################
#
# subclasses (both abstract and concrete) that descend from Persistable
#

class Subscription(Persistable):  pass

class AllowedAttributeValue(Persistable):  pass  # only used in an AttributeDefinition
class AllowedQueryOperator (Persistable):  pass  # only used in an AttributeDefinition 
                                                 #  (for AllowedQueryOperators)

class DomainObject(Persistable):
    """ This is an Abstract Base class """
    pass

class User            (DomainObject): pass
class UserProfile     (DomainObject): pass
class Workspace       (DomainObject): pass
class Blocker         (DomainObject): pass
class UserPermission  (DomainObject): pass
class WorkspacePermission   (UserPermission): pass
class ProjectPermission     (UserPermission): pass

class WorkspaceDomainObject(DomainObject):
    """ 
        This is an Abstract Base class, with a convenience method (details) that  
        formats the attrbutes and corresponding values into an easily viewable
        mulitiline string representation.
    """
    COMMON_ATTRIBUTES = ['_type', 
                         'oid', 'ref', 'ObjectID', '_ref', 
                         '_CreatedAt', '_hydrated', 
                         'Name', 'Subscription', 'Workspace', 
                         'FormattedID'
                        ]

    def details(self):
        """
            order we want to have the attributes appear in...

            Class Name (aka _type)
                oid
                ref
                _ref
                _hydrated
                _CreatedAt
                ObjectID
                Name         ** not all items will have this...
                Subscription (oid, Name)
                Workspace    (oid, Name)
                FormattedID   ** not all items will have this...

                alphabetical from here on out
        """
        tank = ['%s' % self._type]
        for attribute_name in self.COMMON_ATTRIBUTES[1:]:
            try:
                value = getattr(self, attribute_name)
            except AttributeError:
                continue
            if value is None:
                continue
            if 'pyral.entity.' not in str(type(value)):
                anv = '    %-20s  : %s' % (attribute_name, value)
            else:
                mo = re.search(r' \'pyral.entity.(\w+)\'>', str(type(value)))
                if mo:
                    cln = mo.group(1)
                    anv = "    %-20s  : %-20.20s   (OID  %s  Name: %s)" % \
                          (attribute_name, cln + '.ref', value.oid, value.Name)
                else:
                    anv = "    %-20s  : %s" % value
            tank.append(anv)
        tank.append("")
        other_attributes = set(self.attributes()) - set(self.COMMON_ATTRIBUTES)
        for attribute_name in sorted(other_attributes):
            #value = getattr(self, attribute_name)
            #
            # bypass any attributes that the item might have but doesn't have 
            # as a query fetch clause may have been False or didn't include the attribute
            try: 
                value = getattr(self, attribute_name)
            except AttributeError: 
                continue
            if not isinstance(value, Persistable):
                anv = "    %-20s  : %s" % (attribute_name, value)
            else:
                mo = re.search(r' \'pyral.entity.(\w+)\'>', str(type(value)))
                if not mo:
                    anv = "    %-20s : %s" % (attribute_name, value)
                    continue

                cln = mo.group(1)
                anv = "    %-20s  : %-27.27s" % (attribute_name, cln + '.ref')
                if   isinstance(value, Artifact):
                    # also want the OID, FormattedID
                    anv = "%s (OID  %s  FomattedID  %s)" % (anv, value.oid, value.FormattedID)
                elif isinstance(value, User):
                    # also want the className, OID, UserName, DisplayName
                    anv = "    %-20s  : %s.ref  (OID  %s  UserName %s  DisplayName %s)" % \
                          (attribute_name, cln, value.oid, value.UserName, value.DisplayName)
                else:
                    # also want the className, OID, Name)
                    anv = "%s (OID  %s  Name %s)" % (anv, value.oid, value.Name)
            tank.append(anv)
        return "\n".join(tank)


class WorkspaceConfiguration(WorkspaceDomainObject): pass
class Type                  (WorkspaceDomainObject): pass
class Program               (WorkspaceDomainObject): pass
class Project               (WorkspaceDomainObject): pass
class Release               (WorkspaceDomainObject): pass
class Iteration             (WorkspaceDomainObject): pass
class Revision              (WorkspaceDomainObject): pass
class RevisionHistory       (WorkspaceDomainObject): pass
class SCMRepository         (WorkspaceDomainObject): pass
class AttributeDefinition   (WorkspaceDomainObject): pass  # query capable only
class TypeDefinition        (WorkspaceDomainObject): pass  # query capable only
class Attachment            (WorkspaceDomainObject): pass
class AttachmentContent     (WorkspaceDomainObject): pass
class Build                 (WorkspaceDomainObject): pass  # query capable only
class BuildDefinition       (WorkspaceDomainObject): pass  # query capable only
class BuildMetric           (WorkspaceDomainObject): pass  # query capable only
class BuildMetricDefinition (WorkspaceDomainObject): pass  # query capable only
class Change                (WorkspaceDomainObject): pass
class Changeset             (WorkspaceDomainObject): pass
class ConversationPost      (WorkspaceDomainObject): pass  # query capable only
class TestCaseStep          (WorkspaceDomainObject): pass
class TestCaseResult        (WorkspaceDomainObject): pass
class TestFolder            (WorkspaceDomainObject): pass
class Tag                   (WorkspaceDomainObject): pass
class Preference            (WorkspaceDomainObject): pass
class TimeEntryItem         (WorkspaceDomainObject): pass
class TimeEntryValue        (WorkspaceDomainObject): pass
class PreliminaryEstimate   (WorkspaceDomainObject): pass
class State                 (WorkspaceDomainObject): pass

class WebLinkDefinition(AttributeDefinition): pass

class CumulativeFlowData(WorkspaceDomainObject):
    """ This is an Abstract Base class """
    pass

class ReleaseCumulativeFlowData  (CumulativeFlowData): pass
class IterationCumulativeFlowData(CumulativeFlowData): pass

class Artifact(WorkspaceDomainObject): 
    """ This is an Abstract Base class """
    pass

class Task         (Artifact): pass
class Defect       (Artifact): pass
class DefectSuite  (Artifact): pass
class TestCase     (Artifact): pass
class TestSet      (Artifact): pass
class PortfolioItem(Artifact): pass
class Requirement  (Artifact):
    """ This is an Abstract Base class """
    pass
class HierarchicalRequirement(Requirement): pass

UserStory = HierarchicalRequirement   # synonomous but more intutive
Story     = HierarchicalRequirement   # ditto

class CustomField(object):  
    """
        For non-Rally originated entities

        TBD: does this need the __getattr__ hook also?
    """
    def __init__(self, oid, name, resource_url, context):
        """
        """
        self.oid = oid
        self.Name = name
        self._ref = resource_url
        self._context  = context
        self._hydrated = False

#################################################################################################

# ultimately, the classFor dict is what is intended to be exposed as a means to limit
# instantiation to concrete classes, although because of dyna-types that is no longer
# very strictly enforced
# 

classFor = { 'WorkspaceDomainObject'   : WorkspaceDomainObject,
             'Subscription'            : Subscription,
             'User'                    : User,
             'UserProfile'             : UserProfile,
             'UserPermission'          : UserPermission,
             'Workspace'               : Workspace,
             'WorkspaceConfiguration'  : WorkspaceConfiguration,
             'WorkspacePermission'     : WorkspacePermission,
             'Type'                    : Type,
             'TypeDefinition'          : TypeDefinition,
             'AttributeDefinition'     : AttributeDefinition,
             'Program'                 : Program,
             'Project'                 : Project,
             'ProjectPermission'       : ProjectPermission,
             'Release'                 : Release,
             'Iteration'               : Iteration,
             'HierarchicalRequirement' : HierarchicalRequirement,
             'UserStory'               : UserStory,
             'Story'                   : Story,
             'Task'                    : Task,
             'Tag'                     : Tag,
             'Preference'              : Preference,
             'SCMRepository'           : SCMRepository,
             'Revision'                : Revision,
             'RevisionHistory'         : RevisionHistory,
             'Attachment'              : Attachment,
             'AttachmentContent'       : AttachmentContent,
             'TestCase'                : TestCase,
             'TestCaseStep'            : TestCaseStep,
             'TestCaseResult'          : TestCaseResult,
             'TestSet'                 : TestSet,
             'TestFolder'              : TestFolder,
             'TimeEntryItem'           : TimeEntryItem,
             'TimeEntryValue'          : TimeEntryValue,
             'Build'                   : Build,
             'BuildDefinition'         : BuildDefinition,
             'BuildMetric'             : BuildMetric,
             'BuildMetricDefinition'   : BuildMetricDefinition,
             'Defect'                  : Defect,
             'DefectSuite'             : DefectSuite,
             'Change'                  : Change,
             'Changeset'               : Changeset,
             'PortfolioItem'           : PortfolioItem,
             'State'                   : State,
             'PreliminaryEstimate'     : PreliminaryEstimate,
             'WebLinkDefinition'       : WebLinkDefinition,
             'ConversationPost'        : ConversationPost,
             'Blocker'                 : Blocker,
             'AllowedAttributeValue'   : AllowedAttributeValue,
             'AllowedQueryOperator'    : AllowedQueryOperator,
             'CustomField'             : CustomField,
             'ReleaseCumulativeFlowData'   : ReleaseCumulativeFlowData,
             'IterationCumulativeFlowData' : IterationCumulativeFlowData,
           }

for entity_name, entity_class in classFor.items():
    _rally_entity_cache[entity_name] = entity_name
entity_class = None # reset...

# now stuff whatever other classes we've defined in this module that aren't already in 
# _rally_entity_cache

# Predicate to make sure the classes only come from the module in question
def pred(c):
    return inspect.isclass(c) and c.__module__ == pred.__module__
# fetch all members of module __name__ matching 'pred'
import inspect
classes = inspect.getmembers(sys.modules[__name__], pred)
for cls_name, cls in classes:
    if cls_name not in _rally_entity_cache and re.search("^[A-Z]", cls_name):
        _rally_entity_cache[cls_name] = cls_name

##################################################################################################

def getEntityName(candidate):
    """
    """
    global _rally_entity_cache

    official_name = candidate
    # look for an entry in _rally_entity_cache of the form '*/candidate'
    # and use that as the official_name if such an entry exists
    hits = [path for entity, path in _rally_entity_cache.items()
                    #if re.match("^.*/%s$" % candidate, candidate)]
                    if '/' in path and path.split('/')[1] == candidate]
##
##    print "for candidate |%s|  hits: |%s|" % (candidate, hits)
##
    if hits:
        official_name = hits.pop(0)
    return official_name


def validRallyType(rally, candidate):
    """
        Given an instance of Rally and a candidate Rally entity name,
        see if the candidate is in our _rally_entity_cache by virtue
        of this module's initialization.  If not, and we haven't augmented
        the cache yet, augment the cache and try to determine if it is
        a valid ElementName and if so, return the ElementName or TypePath.
        Raise an exception when the candidate cannot be determined to be
        the ElementName of a valid Rally Type.
    """
    global _rally_entity_cache, _typedefs_slurped
##
##    print "checking validity of Rally Type name: |%s|" % candidate
##

    if candidate in _rally_entity_cache: 
##
##        print "   candidate in _rally_entity_cache,  value: |%s|" % _rally_entity_cache[candidate]
##
        return getEntityName(candidate)

    if not _typedefs_slurped:
        retrieveAllTypeDefinitions(rally)
        _typedefs_slurped = True
    
    if candidate not in _rally_entity_cache:
        raise InvalidRallyTypeNameError(candidate)
    
    return getEntityName(candidate)


def retrieveAllTypeDefinitions(rally):
    """
    """
    global _rally_entity_cache
    global classFor

    response = rally.get('TypeDefinition', fetch='ElementName,Parent,TypePath,Name',
                                           order="Name",
                                           project=None)
    for td in response:
        elementName = str(td.ElementName) # d*mn unicode defensiveness manuever
        if elementName.startswith('ObjectAttr'):
            continue
        if elementName not in _rally_entity_cache:
            #
            # If there isn't an entry in _rally_entity_cache, dynamically create 
            # the class subclassed the Parent (or Artifact) and stuff an entry in 
            # classFor for it in addition to marking the _rally_entity_cache
            #
            parentElement = None
            if td.Parent:
                parentElement = str(td.Parent.ElementName)
            parent = parentElement or 'Artifact'
            parentClass = classFor[parent]
            rally_entity_class = _createClass(elementName, parentClass)
            classFor[elementName] = rally_entity_class
            _rally_entity_cache[elementName] = elementName
            if '/' in str(td.TypePath):
                _rally_entity_cache[str(td.TypePath)] = elementName
                _rally_entity_cache[elementName]      = str(td.TypePath)
##
#    for key, value in _rally_entity_cache.items():
#        if '/' in value:
#            print "...key  |%s|  value |%s|" % (key, value)
##


def _createClass(name, parentClass):
    """
        Dynamically create a class named for name whose parent is parent, and
        make the newly created class available by name in the global namespace.
    """
    rally_entity_class = type(name, (parentClass,), {})
    
    globals()[name] = rally_entity_class
    return rally_entity_class


__all__ = [validRallyType, classFor, InvalidRallyTypeNameError]
