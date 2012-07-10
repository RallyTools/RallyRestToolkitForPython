
###################################################################################################
#
#  pyral.entity - defines the entities in Rally, exposes a classFor dict
#                 to allow instantiation of concrete Rally entities
#          dependencies:
#               intra-package: the getResourceByOID and hydrateAnInstance functions from restapi
#
###################################################################################################

__version__ = (0, 9, 1)

import sys
import re

from .restapi   import hydrateAnInstance
from .restapi   import getResourceByOID

##################################################################################################

VERSION_ATTRIBUTES = ['_rallyAPIMajor', '_rallyAPIMinor', '_objectVersion']
MINIMAL_ATTRIBUTES = ['_type', '_ref', '_refObjectName']

##################################################################################################

class UnreferenceableOIDError(Exception): 
    """
        An Exception to be raised in the case where an Entity/OID pair in a _ref field
        cannot be retrieved.
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
                raise UnreferenceableOIDError, ("%s OID %s" % (rallyEntityTypeName, self.oid))
            if not isinstance(response, object): # TODO: would like to be specific with RallyRESTResponse here...
                print "bad guess on response type in __getattr__, response is a %s" % type(response)
                raise UnreferenceableOIDError, ("%s OID %s" % (rallyEntityTypeName, self.oid))
            if response.status_code != 200:
                raise UnreferenceableOIDError, ("%s OID %s" % (rallyEntityTypeName, self.oid))
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
            raise AttributeError, "%s instance has no attribute: '%s'" % (rallyEntityTypeName, name)

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
                         'ObjectID', '_ref', '_CreatedAt', 
                         'oid', 'ref', '_hydrated', 
                         'Name', 'Subscription', 'Workspace'
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

                alphabetical from here on out
        """
        tank = ['%s' % self._type]
        for attribute_name in self.COMMON_ATTRIBUTES[1:]:
            value = getattr(self, attribute_name)
            if 'pyral.entity.' not in str(type(value)):
                anv = '    %-16.16s  : %s' % (attribute_name, value)
            else:
                mo = re.search(r' \'pyral.entity.(\w+)\'>', str(type(value)))
                if mo:
                    cln = mo.group(1)
                    anv = "    %-16.16s  : %-16.16s   (OID  %s  Name: %s)" % \
                          (attribute_name, cln + '.ref', value.oid, value.Name)
                else:
                    anv = "    %-16.16s  : %s" % value
            tank.append(anv)
        tank.append("")
        other_attributes = set(self.attributes()) - set(self.COMMON_ATTRIBUTES)
        for attribute_name in sorted(other_attributes):
            value = getattr(self, attribute_name)
            if not isinstance(value, Persistable):
                anv = "    %-16.16s  : %s" % (attribute_name, value)
            else:
                mo = re.search(r' \'pyral.entity.(\w+)\'>', str(type(value)))
                if not mo:
                    anv = "    %-16.16s : %s" % (attribute_name, value)
                    continue

                cln = mo.group(1)
                anv = "    %-16.16s  : %-27.27s" % (attribute_name, cln + '.ref')
                if   isinstance(value, Artifact):
                    # also want the OID, FormattedID
                    anv = "%s (OID  %s  FomattedID  %s)" % (anv, value.oid, value.FormattedID)
                elif isinstance(value, User):
                    # also want the className, OID, UserName, DisplayName
                    anv = "    %-16.16s  : %s.ref  (OID  %s  UserName %s  DisplayName %s)" % \
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

class WebLinkDefinition(AttributeDefinition): pass

class CumulativeFlowData(WorkspaceDomainObject):
    """ This is an Abstract Base class """
    pass

class ReleaseCumulativeFlow  (CumulativeFlowData): pass
class IterationCumulativeFlow(CumulativeFlowData): pass

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
# instantiation to concrete classes

classFor = { 'Subscription'            : Subscription,
             'User'                    : User,
             'UserProfile'             : UserProfile,
             'UserPermission'          : UserPermission,
             'Workspace'               : Workspace,
             'WorkspaceConfiguration'  : WorkspaceConfiguration,
             'WorkspacePermission'     : WorkspacePermission,
             'Type'                    : Type,
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
             'ReleaseCumulativeFlow'   : ReleaseCumulativeFlow,
             'IterationCumulativeFlow' : IterationCumulativeFlow,
             'Build'                   : Build,
             'BuildDefinition'         : BuildDefinition,
             'BuildMetric'             : BuildMetric,
             'BuildMetricDefinition'   : BuildMetricDefinition,
             'Defect'                  : Defect,
             'DefectSuite'             : DefectSuite,
             'Change'                  : Change,
             'Changeset'               : Changeset,
             'PortfolioItem'           : PortfolioItem,
             'PreliminaryEstimate'     : PreliminaryEstimate,
             'AttributeDefinition'     : AttributeDefinition,
             'TypeDefinition'          : TypeDefinition,
             'WebLinkDefinition'       : WebLinkDefinition,
             'ConversationPost'        : ConversationPost,
             'Blocker'                 : Blocker,
             'AllowedAttributeValue'   : AllowedAttributeValue,
             'AllowedQueryOperator'    : AllowedQueryOperator,
             'CustomField'             : CustomField,
           }

##################################################################################################

