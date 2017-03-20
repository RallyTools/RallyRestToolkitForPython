
###################################################################################################
#
#  pyral.entity - defines the entities in Rally, exposes a classFor dict
#                 to allow instantiation of concrete Rally entities
#          dependencies:
#               intra-package: the getResourceByOID and hydrateAnInstance functions from restapi
#
###################################################################################################

__version__ = (1, 2, 4)

import sys
import re
import types
import time

from .restapi   import hydrateAnInstance
from .restapi   import getResourceByOID
from .restapi   import getCollection

from .config    import WEB_SERVICE, WS_API_VERSION

##################################################################################################

VERSION_ATTRIBUTES = ['_rallyAPIMajor', '_rallyAPIMinor', '_objectVersion']
MINIMAL_ATTRIBUTES = ['_type', '_ref', '_refObjectName']
PORTFOLIO_ITEM_SUB_TYPES = ['Strategy', 'Theme', 'Initiative', 'Feature']
SLM_WS_VER = '/%s/' % (WEB_SERVICE % WS_API_VERSION)

_rally_schema       = {}  # keyed by workspace at the first level, then by EntityName
_rally_entity_cache = {}

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
        doesn't resolve to a valid Rally entity.
    """
    pass

class UnrecognizedAllowedValuesReference(Exception):
    """
        An Exception to be raised in the case where a SchemaItemAttribute.AllowedValues
        URL reference does not contain the expected path components.
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
            All sub-classes also have a uuid (ObjectUUID), so it also makes sense
            to provide the attribute storage here.
        """
        try:
            self.oid = int(oid)
        except:
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
        global SLM_WS_VER

        # access to this Entity's ref attribute is a special case and dealt with early in the logic flow
        if name == "ref":
            entity_name, oid = self._ref.split('/')[-2:]  # last two path elements in _ref are entity/oid
            return '%s/%s' % (entity_name, oid)

        if name == 'context':
            raise Exception('Unsupported attempt to retrieve context attribute')

        rallyEntityTypeName = self.__class__.__name__
        PORTFOLIO_PREFIX = 'PortfolioItem_'
        if rallyEntityTypeName.startswith(PORTFOLIO_PREFIX):
            rallyEntityTypeName = re.sub(PORTFOLIO_PREFIX, '', rallyEntityTypeName)
        # previous logic prior to 1.2.2
        #entity_path, oid = self._ref.split(SLM_WS_VER)[-1].rsplit('/', 1)
        #if entity_path.startswith('portfolioitem/'):
        #    rallyEntityTypeName = entity_path.split('/')[-1].capitalize()

        faultTrigger = "getattr fault detected on %s instance for attribute: %s  (hydrated? %s)" % \
                       (rallyEntityTypeName, name, self._hydrated)
##
##        print(faultTrigger)
##        sys.stdout.flush()
##
        if not self._hydrated:
            #
            # get "hydrated" by issuing a GET request for the resource referenced in self._ref
            # and having an EntityHydrator fill out the attributes, !!* on this instance *!!
            #
            entity_name, oid = self._ref.split(SLM_WS_VER)[-1].rsplit('/', 1)
##
##            print("self._ref : %s" % self._ref)
##            print("issuing OID specific get for %s OID: %s " % (entity_name, oid))
##            print("Entity: %s context: %s" % (rallyEntityTypeName, self._context))
##            sys.stdout.flush()
##
            response = getResourceByOID(self._context, entity_name, self.oid, unwrap=True)
            if not response:
                raise UnreferenceableOIDError("%s OID %s" % (rallyEntityTypeName, self.oid))
            if not isinstance(response, object): 
                # TODO: would like to be specific with RallyRESTResponse here...
                #print("bad guess on response type in __getattr__, response is a %s" % type(response))
                raise UnreferenceableOIDError("%s OID %s" % (rallyEntityTypeName, self.oid))
            if response.status_code != 200:
##
##                print(response)
##
                raise UnreferenceableOIDError("%s OID %s" % (rallyEntityTypeName, self.oid))

            if rallyEntityTypeName == 'PortfolioItem':
                actual_item_name = list(response.content.keys())[0]
                if entity_name.split('/')[1].lower() == actual_item_name.lower():
                    item = response.content[actual_item_name]
                else:  # this would be unexpected, but the above getResourceByOID seems to have been successful...
                    item = response.content[actual_item_name]  # take what we're given...
            else:
                item = response.content[rallyEntityTypeName]
            hydrateAnInstance(self._context, item, existingInstance=self)
            self._hydrated = True

        if name in self.attributes():
            return self.__dict__[name]
        # accommodate custom field access by Name (by prefix 'c_' and squishing out any spaces in Name 
        name_with_custom_prefix = "c_%s" % name.replace(' ', '')
        if name_with_custom_prefix in self.attributes():
            return self.__dict__[name_with_custom_prefix]

        # upon initial access of a Collection type field, we have to detect, retrieve the Collection 
        # and then torch the "lazy" evaluation field marker
        coll_ref_field = '__collection_ref_for_%s' % name
        if coll_ref_field in list(self.__dict__.keys()):
            collection_ref = self.__dict__[coll_ref_field]
##
##            print("  chasing %s collection ref: %s" % (name, collection_ref))
##            print("  using this context: %s" % repr(self._context))
##
            collection = getCollection(self._context, collection_ref, _disableAugments=False)
            if name != "RevisionHistory":  # a "normal" Collections field ...
                self.__dict__[name] = [item for item in collection]
            else:  # RevisionHistory is a special case, the initial collection isn't really a Collection
                self.__dict__[name] = self._hydrateRevisionHistory(collection_ref, collection)
            del self.__dict__[coll_ref_field]
            return self.__dict__[name]
        else:
            description = "%s instance has no attribute: '%s'" % (rallyEntityTypeName, name)
##
##            print("Rally entity getattr fault: %s" % description)
##
            raise AttributeError(description)


    def _hydrateRevisionHistory(self, collection_ref, collection):
        """
            A Rally entity's RevisionHistory attribute is a special case, while it "looks" like a
            collection, the results of chasing the collection ref don't result in a "real" collection.
            What comes back contains the ref to the actual "collection" which is the Revisions data,
            so that is retrieved and used to construct the "guts" of RevisionHistory, ie., the Revisions.
        """
        # pull the necessary fragment out from collection query, 
        rev_hist_raw = collection.data['QueryResult']['Results']['RevisionHistory']
        rev_hist_oid = rev_hist_raw['ObjectID']
        revs_ref     = rev_hist_raw['Revisions']['_ref']  # this is the "true" Revisions collection ref
        # create a RevisionHistory instance with oid, Name and _ref field information
        rev_hist = RevisionHistory(rev_hist_oid, 'RevisonHistory', collection_ref, self._context)
        # chase the revs_ref set the RevisionHistory.Revisions attribute with that Revisions collection
        revisions = getCollection(self._context, revs_ref, _disableAugments=False)
        rev_hist.Revisions = [revision for revision in revisions]
        # mark the RevisionHistory instance as being fully hydrated
        rev_hist._hydrated = True
        return rev_hist

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

class User (DomainObject): 
    USER_ATTRIBUTES = ['oid', 'ref', 'ObjectID', 'ObjectUUID', '_ref', 
                       '_CreatedAt', '_hydrated', 
                       'UserName', 'DisplayName', 'EmailAddress', 
                       'FirstName', 'MiddleName', 'LastName', 
                       'ShortDisplayName', 
                       'SubscriptionAdmin',
                       'Role',
                       'UserPermissions',
                       #'TeamMemberships',
                       #'UserProfile'
                      ]
    def details(self):
        """
            Assemble a list of USER_ATTRIBUTES and values 
            and join it into a single string with newline "delimiters".
            Return this string so that the caller can simply print it and have
            a nicely formatted block of information about the specific User.
        """
        tank = ['%s' % self._type]
        for attribute_name in self.USER_ATTRIBUTES[1:]:
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
                    cln = mo.group(1)  # cln -- class name
                    anv = "    %-20s  : %-20.20s   (OID  %s  Name: %s)" % \
                          (attribute_name, cln + '.ref', value.oid, value.Name)
                else:
                    anv = "    %-20s  : %s" % value
            tank.append(anv)
        return "\n".join(tank)

class UserProfile     (DomainObject):
    USER_PROFILE_ATTRIBUTES = ['oid', 'ref', 'ObjectID', 'ObjectUUID', '_ref',
                               '_CreatedAt', '_hydrated', 
                               'DefaultWorkspace', 'DefaultProject',
                               'TimeZone',
                               'DateFormat', 'DateTimeFormat',
                               'SessionTimeoutSeconds', 'SessionTimeoutWarning',
                               'EmailNotificationEnabled', 
                               'WelcomePageHidden'
                              ]
    def details(self):
        """
            Assemble a list of USER_PROFILE_ATTRIBUTES and values 
            and join it into a single string with newline "delimiters".
            Return this string so that the caller can simply print it and have
            a nicely formatted block of information about the specific User.
        """
        tank = ['%s' % self._type]
        for attribute_name in self.USER_PROFILE_ATTRIBUTES[1:]:
            try:
                value = getattr(self, attribute_name)
            except AttributeError:
                continue
            if 'pyral.entity.' not in str(type(value)):
                anv = '    %-24s  : %s' % (attribute_name, value)
            else:
                mo = re.search(r' \'pyral.entity.(\w+)\'>', str(type(value)))
                if mo:
                    cln = mo.group(1)
                    anv = "    %-24s  : %-14.14s   (OID  %s  Name: %s)" % \
                          (attribute_name, cln + '.ref', value.oid, value.Name)
                else:
                    anv = "    %-24s  : %s" % value
            tank.append(anv)
            
        return "\n".join(tank)

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
                         'oid', 'ref', 'ObjectID', 'ObjectUUID', '_ref', 
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
                ObjectUUID
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
                anv = '    %-24s  : %s' % (attribute_name, value)
            else:
                mo = re.search(r' \'pyral.entity.(\w+)\'>', str(type(value)))
                if mo:
                    cln = mo.group(1)
                    anv = "    %-24s  : %-20.20s   (OID  %s  Name: %s)" % \
                          (attribute_name, cln + '.ref', value.oid, value.Name)
                else:
                    anv = "    %-24s  : %s" % (attribute_name, value)
            tank.append(anv)
        tank.append("")
        other_attributes = set(self.attributes()) - set(self.COMMON_ATTRIBUTES)
##
##        print("other_attributes: %s" % ", ".join(other_attributes))
##
        for attribute_name in sorted(other_attributes):
            #value = getattr(self, attribute_name)
            #
            # bypass any attributes that the item might have but doesn't have 
            # as a query fetch clause may have been False or didn't include the attribute
            try: 
                value = getattr(self, attribute_name)
            except AttributeError: 
##
##                print("  unable to getattr for |%s|" % attribute_name)
##
                continue
            attr_name = attribute_name
            if attribute_name.startswith('c_'):
                attr_name = attribute_name[2:]
            if not isinstance(value, Persistable):
                anv = "    %-24s  : %s" % (attr_name, value)
            else:
                mo = re.search(r' \'pyral.entity.(\w+)\'>', str(type(value)))
                if not mo:
                    anv = "    %-24s : %s" % (attr_name, value)
                    continue

                cln = mo.group(1)
                anv = "    %-24s  : %-27.27s" % (attr_name, cln + '.ref')
                if   isinstance(value, Artifact):
                    # also want the OID, FormattedID
                    anv = "%s (OID  %s  FomattedID  %s)" % (anv, value.oid, value.FormattedID)
                elif isinstance(value, User):
                    # also want the className, OID, UserName, DisplayName
                    anv = "    %-24s  : %s.ref  (OID  %s  UserName %s  DisplayName %s)" % \
                          (attr_name, cln, value.oid, value.UserName, value.DisplayName)
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
class Iteration             (WorkspaceDomainObject): pass  # query capable only
class ArtifactNotification  (WorkspaceDomainObject): pass  # query capable only
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
class Milestone             (WorkspaceDomainObject): pass 
class Preference            (WorkspaceDomainObject): pass
class PreliminaryEstimate   (WorkspaceDomainObject): pass
class SCMRepository         (WorkspaceDomainObject): pass
class State                 (WorkspaceDomainObject): pass
class TestCaseStep          (WorkspaceDomainObject): pass
class TestCaseResult        (WorkspaceDomainObject): pass
class TestFolder            (WorkspaceDomainObject): pass
class Tag                   (WorkspaceDomainObject): pass
class TimeEntryItem         (WorkspaceDomainObject): pass
class TimeEntryValue        (WorkspaceDomainObject): pass
class UserIterationCapacity (WorkspaceDomainObject): pass
class RecycleBinEntry       (WorkspaceDomainObject): pass
class RevisionHistory       (WorkspaceDomainObject): pass
class Revision              (WorkspaceDomainObject):
    INFO_ATTRS = ['RevisionNumber', 'Description', 'CreationDate', 'User']
    def info(self):
        rev_num = self.RevisionNumber
        desc    = self.Description
        activity_timestamp = self.CreationDate
        whodunit = self.User.Name  # self.User.UserName # can't do UserName as context is incomplete...
        rev_blurb = "   %3d on %s by %s\n             %s" % (rev_num, activity_timestamp, whodunit, desc)
        return rev_blurb

class WebLinkDefinition(AttributeDefinition): pass

class CumulativeFlowData(WorkspaceDomainObject):
    """ This is an Abstract Base class """
    pass

class ReleaseCumulativeFlowData  (CumulativeFlowData): pass
class IterationCumulativeFlowData(CumulativeFlowData): pass

class Artifact(WorkspaceDomainObject): 
    """ This is an Abstract Base class """
    pass

class SchedulableArtifact(Artifact):
    """ This is an Abstract Base class """ 
    pass

class Requirement  (SchedulableArtifact):
    """ This is an Abstract Base class """
    pass
class HierarchicalRequirement(Requirement): pass

UserStory = HierarchicalRequirement   # synonomous but more intutive
Story     = HierarchicalRequirement   # ditto

class Task         (Artifact): pass
class Defect       (Artifact): pass
class TestCase     (Artifact): pass
class DefectSuite  (SchedulableArtifact): pass
class TestSet      (SchedulableArtifact): pass

class PortfolioItem(Artifact): pass
class PortfolioItem_Strategy  (PortfolioItem): pass
class PortfolioItem_Initiative(PortfolioItem): pass
class PortfolioItem_Theme     (PortfolioItem): pass
class PortfolioItem_Feature   (PortfolioItem): pass

class CustomField(object):  
    """
        For non-Rally originated entities

        TBD: does this need the __getattr__ hook also?
    """
    def __init__(self, oid, name, resource_url, context):
        """
        """
        self.oid = int(oid)
        self.Name = name
        self._ref = resource_url
        self._context  = context
        self._hydrated = False

def so_element_text(mo):
    #if mo: return mo.group('field_name') + ': '
    #else: return ""
    return mo.group('field_name') + ': 'if mo else ""

def so_bolded_text(mo):
    #if mo: return "<bold>%s</bold>" % mo.group('word')
    #else: return ""
    return "<bold>%s</bold>" % mo.group('word') if mo else ""

class SearchObject(object): 
    """
        An instance of SearchObject is created for each artifact that
        matches a search criteria.  A SearchObject is not a full-fledged
        artifact however, it only has minimal identifying attributes and
        snippets from each string field that contained text that matched
        a part of the search criteria.
    """

    tagged_field_name_pattern = re.compile(r'<span class=\'alm-search-page matching-text-field-name\'>(?P<field_name>.*?): </span>')
                                         #   <span class='alm-search-page matching-text-field-name'>Discussion: </span>
    bolding_pattern = re.compile(r'<span id="keepMeBolded" class="alm-search-page matching-text-highlight">(?P<word>.*?)</span>')
                               #   <span id="keepMeBolded" class="alm-search-page matching-text-highlight">bogus</span>

    def __init__(self, oid, name, resource_url, context):
        """
            All sub-classes have an oid (Object ID), so it makes sense to provide the 
            attribute storage here.
        """
        self.oid = self.ObjectID = int(oid)
        self.Name = name
        self._ref = resource_url
        self._hydrated = True
        self._context = context

    def __setattr__(self, item, value):
        self.__dict__[item] = value
        if item == 'MatchingText':
            # scrub out the alm specific html tags 
            scrubbed = re.sub(self.tagged_field_name_pattern, so_element_text, value)
            scrubbed = re.sub(self.bolding_pattern, so_bolded_text, scrubbed)
            self.__dict__[item] = scrubbed
        return self.__dict__[item]

#################################################################################################

# ultimately, the classFor dict is what is intended to be exposed as a means to limit
# instantiation to concrete classes, although because of dyna-types that is no longer
# very strictly enforced
# 

classFor = { 'Persistable'             : Persistable,
             'DomainObject'            : DomainObject,
             'WorkspaceDomainObject'   : WorkspaceDomainObject,
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
             'Artifact'                : Artifact,
             'ArtifactNotification'    : ArtifactNotification,
             'Release'                 : Release,
             'Iteration'               : Iteration,
             'Requirement'             : Requirement,
             'HierarchicalRequirement' : HierarchicalRequirement,
             'UserStory'               : UserStory,
             'Story'                   : Story,
             'Task'                    : Task,
             'Tag'                     : Tag,
             'Preference'              : Preference,
             'SCMRepository'           : SCMRepository,
             'RevisionHistory'         : RevisionHistory,
             'Revision'                : Revision,
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
             'PortfolioItem_Strategy'  : PortfolioItem_Strategy,
             'PortfolioItem_Initiative': PortfolioItem_Initiative,
             'PortfolioItem_Theme'     : PortfolioItem_Theme,
             'PortfolioItem_Feature'   : PortfolioItem_Feature,
             'State'                   : State,
             'PreliminaryEstimate'     : PreliminaryEstimate,
             'WebLinkDefinition'       : WebLinkDefinition,
             'Milestone'               : Milestone,
             'ConversationPost'        : ConversationPost,
             'Blocker'                 : Blocker,
             'AllowedAttributeValue'   : AllowedAttributeValue,
             'AllowedQueryOperator'    : AllowedQueryOperator,
             'CustomField'             : CustomField,
             'UserIterationCapacity'   : UserIterationCapacity,
             'CumulativeFlowData'      : CumulativeFlowData,
             'ReleaseCumulativeFlowData'   : ReleaseCumulativeFlowData,
             'IterationCumulativeFlowData' : IterationCumulativeFlowData,
             'RecycleBinEntry'         : RecycleBinEntry,
             'SearchObject'            : SearchObject,
           }

for entity_name, entity_class in list(classFor.items()):
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

class SchemaItem(object):
    def __init__(self, raw_info):
        self._type = 'TypeDefinition'
        # ElementName, DisplayName, Name
        # Ordinal   # who knows what is for... looks to be only relevant for PortfolioItem sub-items
        # ObjectID, 
        # Parent, Abstract, TypePath, IDPrefix, 
        # Creatable, ReadOnly, Queryable, Deletable, Restorable
        # Attributes
        # RevisionHistory
        # Subscription, Workspace
        self.ref    = "/".join(raw_info['_ref'].split('/')[-2:])
        self.ObjectName  = str(raw_info['_refObjectName'])
        self.ElementName = str(raw_info['ElementName'])
        self.Name        = str(raw_info['Name'])
        self.DisplayName = str(raw_info['DisplayName'])
        self.TypePath    = str(raw_info['TypePath'])
        self.IDPrefix    = str(raw_info['IDPrefix'])
        self.Abstract    =     raw_info['Abstract']
        self.Parent      =     raw_info['Parent']
        if self.Parent:  # so apparently AdministratableProject doesn't have a Parent object
            self.Parent = str(self.Parent['_refObjectName'])
        self.Creatable   =     raw_info['Creatable']
        self.Queryable   =     raw_info['Queryable']
        self.ReadOnly    =     raw_info['ReadOnly']
        self.Deletable   =     raw_info['Deletable']
        self.Restorable  =     raw_info['Restorable']
        self.Ordinal     =     raw_info['Ordinal']
        self.RevisionHistory = raw_info['RevisionHistory'] # a ref to a Collection, defer chasing for now...
        self.Attributes  = []
        for attr in raw_info['Attributes']:
            self.Attributes.append(SchemaItemAttribute(attr))
        self.completed = False


    def complete(self, context, getCollection):
        """
            This method is used to trigger the complete population of all Attributes,
            in particular the resolution of refs to AllowedValues that are present after
            the instantation of each Attribute.  
            Sequence through each Attribute and call resolveAllowedValues for each Attribute.
        """
        if self.completed:
            return True
        for attribute in sorted([attr for attr in self.Attributes if attr.AttributeType in ['RATING', 'STATE']]):
            # only an attribute whose AttributeType is RATING or STATE will have allowedValues
            attribute.resolveAllowedValues(context, getCollection)

        self.completed = True
        return self.completed


    def inheritanceChain(self):
        """
            Find the chain of inheritance for this Rally Type.
            Exclude the basic Python object. 
            Return a list starting with the furthermost ancestor continuing on down to this Rally Type.
        """
        try:
            klass = classFor[self.Name.replace(' ', '')]
        except:
            pi_qualified_name = 'PortfolioItem_%s' % self.Name
            try:
                klass = classFor[pi_qualified_name.replace(' ', '')]
            except:
                raise InvalidRallyTypeNameError(self.Name)

        ancestors = []
        for ancestor in klass.mro():
            mo = re.search(r"'pyral\.entity\.(\w+)'", str(ancestor))
            if mo:
                ancestors.append(mo.group(1))
        ancestors.reverse()
        return ancestors


    def __str__(self):
        """
            Apparently no items returned by the WSAPI 2.0 have Abstract == True, 
            so don't include it in the output string.
            Also, the Parent info is essentially a duplicate of ElementName except for PortfolioItem sub-items,
            so exclude that info from the output string, we'll cover this by handling the TypePath instead.
            For the TypePath, only include that if the string contains a '/' character, in which case
            include that on the head_line.
        """
        abstract   = "Abstract" if self.Abstract else "Concrete"
        parentage  = "Parent -> %s" % self.Parent if self.Parent != self.ElementName else ""
        abs_par    = "    %s  %s" % (abstract, parentage)
        tp         = "TypePath: %s" % self.TypePath if '/' in self.TypePath else ""
        head_line  = "%s  DisplayName: %s  IDPrefix: %s  %s"  % \
                     (self.ElementName, self.DisplayName, self.IDPrefix, tp)
        creatable  = "Creatable"  if self.Creatable  else "Non-Creatable"
        read_only  = "ReadOnly"   if self.ReadOnly   else "Updatable"
        queryable  = "Queryable"  if self.Queryable  else "Non-Queryable"
        deletable  = "Deletable"  if self.Deletable  else "Non-Deletable"
        restorable = "Restorable" if self.Restorable else "Non-Restorable"
        ops_line   = "      %s  %s  %s  %s  %s" % (creatable, read_only, queryable, deletable, restorable)
        attr_hdr   = "      Attributes:"
        attrs      = [str(attr)+"\n" for attr in self.Attributes]

        general = "\n".join([head_line, ops_line, "", attr_hdr])

        return general + "\n" + "\n".join(attrs) 

class SchemaItemAttribute(object):
    def __init__(self, attr_info):
        self._type    = "AttributeDefinition"
        self.ref      = "/".join(attr_info['_ref'][-2:])
        self.ObjectName    = str(attr_info['_refObjectName'])
        self.ElementName   = str(attr_info['ElementName'])
        self.Name          = str(attr_info['Name'])
        self.AttributeType = str(attr_info['AttributeType'])
        self.Subscription  =     attr_info.get('Subscription', None) # not having 'Subscription' should be rare
        self.Workspace     =     attr_info.get('Workspace', None) # apparently only custom fields will have a 'Workspace' value
        self.Custom        =     attr_info['Custom']
        self.Required      =     attr_info['Required']
        self.ReadOnly      =     attr_info['ReadOnly']
        self.Filterable    =     attr_info['Filterable']
        self.Hidden        =     attr_info['Hidden']
        self.SchemaType    =     attr_info['SchemaType']
        self.Constrained   =     attr_info['Constrained']
        self.AllowedValueType =  attr_info['AllowedValueType'] # has value iff this attribute has allowed values
        self.AllowedValues    =  attr_info['AllowedValues']
        self.MaxLength        =  attr_info['MaxLength']
        self.MaxFractionalDigits = attr_info['MaxFractionalDigits']
        self._allowed_values           =  False
        self._allowed_values_resolved  =  False
        if self.AllowedValues and type(self.AllowedValues) == dict:
            self.AllowedValues = str(self.AllowedValues['_ref']) # take the ref as value
            self._allowed_values = True
        elif self.AllowedValues and type(self.AllowedValues) == list:
            buffer = []
            for item in self.AllowedValues:
                aav = AllowedAttributeValue(0, item['StringValue'], None, None)
                aav.Name        = item['StringValue']
                aav.StringValue = item['StringValue']
                aav._hydrated   = True
                buffer.append(aav)
            self.AllowedValues = buffer[:]
            self._allowed_values = True
            self._allowed_values_resolved = True

    def __lt__(self, other):
        return self.ElementName < other.ElementName

    def resolveAllowedValues(self, context, getCollection):
        """
            Only if this Attribute has AllowedValues and those values have not yet been obtained
            by chasing the collection URL left from initialization, does this method issue a
            call to resolve the collection URL via the getCollection callable parm.
            The need to use getCollection is based on whether the AllowedValues value 
            is a string that matches the regex '^https?://.*/attributedefinition/-\d+/AllowedValues'
        """
##
##        print("in resolveAllowedValues for |%s| is a %s" % (self.Name, type(self.Name)))
##        print("in resolveAllowedValues for %s   AllowedValues: %s" % (self.Name, self.AllowedValues))
##
        if not self._allowed_values:
            self._allowed_values_resolved = True
            return True
        if self._allowed_values_resolved:
            return True
        if type(self.AllowedValues) != str:  #previously was   != bytes
            return True
        std_av_ref_pattern = '^https?://.*/\w+/-?\d+/AllowedValues$'
        mo = re.match(std_av_ref_pattern, self.AllowedValues)
        if not mo:
            anomaly = "Standard AllowedValues ref pattern |%s| not matched by candidate |%s|" % \
                      (std_av_ref_pattern, self.AllowedValues)
            raise UnrecognizedAllowedValuesReference(anomaly)
##        
##        print("about to call getCollection for %s  on %s" % (self.AllowedValues, self.Name))
##        
        collection = getCollection(context, self.AllowedValues)
        self.AllowedValues = [value for value in collection]
        self._allowed_values_resolved = True

        return True


    def __str__(self):
        ident = self.ElementName
        disp  = "|%s|" % self.Name if self.Name != self.ElementName else ""
        custom = "" if not self.Custom else "Custom"
        attr_type = self.AttributeType
        required = "Required"  if self.Required    else "Optional"
        ident_line = "         %-24.24s  %-6.6s  %10.10s  %8.8s  %s" % (ident, custom, attr_type, required, disp)
        ro     = "ReadOnly"    if self.ReadOnly    else "Updatable"
        filt   = "Filterable"  if self.Filterable  else ""
        hidden = "Hidden"      if self.Hidden      else ""
        constr = "Constrained" if self.Constrained else ""
        misc_line  = "             %s  %s  %s  %s" % (ro, filt, hidden, constr)
        st_line    = "             SchemaType: %s" % self.SchemaType

        output_lines = [ident_line, misc_line]

        if self.AllowedValueType and not self._allowed_values_resolved:
            avt_ref = "/".join(self.AllowedValueType['_ref'].split('/')[-2:])
            avt_line = "             AllowedValueType ref: %s" % avt_ref
            #output_lines.append(avt_line)
            avv_ref = "/".join(self.AllowedValues.split('/')[-3:])
            avv_line = "             AllowedValues: %s" % avv_ref
            output_lines.append(avv_line)
        elif self._allowed_values_resolved:
            if self.AllowedValues and type(self.AllowedValues) == list:
                avs = []
                for ix, item in enumerate(self.AllowedValues):
                   if type(item) == dict:
                       avs.append(str(item['StringValue']))
                   else:
                       avs.append(str(item.__dict__['StringValue']))

                avv_line = "             AllowedValues: %s" % avs
                output_lines.append(avv_line)

        return "\n".join(output_lines)

##################################################################################################

def getEntityName(candidate):
    """
        Looks for an entry in the _rally_entity_cache of the form '*/candidate'
        and returns that value if it exists.
    """
    global _rally_entity_cache

    official_name = candidate
    hits = [path for entity, path in list(_rally_entity_cache.items())
                    if '/' in path and path.split('/')[1] == candidate]
##
##    print("for candidate |%s|  hits: |%s|" % (candidate, hits))
##
    if hits:
        official_name = hits.pop(0)
    return official_name


def validRallyType(candidate):
    """
        Given a candidate Rally entity name, see if the candidate is in our 
        _rally_entity_cache by virtue of being populated via a startup call
        to processSchemaInfo.
        Raise an exception when the candidate cannot be determined to be
        the ElementName of a valid Rally Type.
    """
    global _rally_entity_cache

    if candidate in _rally_entity_cache:
        return getEntityName(candidate)

    # Unfortunate hard-coding of standard Rally Portfolio item dyna-types
    if candidate in PORTFOLIO_ITEM_SUB_TYPES:
        pi_candidate = 'PortfolioItem/%s' % candidate
        return getEntityName(pi_candidate)

    raise InvalidRallyTypeNameError(candidate)


def processSchemaInfo(workspace, schema_info):
    """
        Fill _rally_schema dict for the workspace's ref key with a dict of 
           SchemaItem objects for each block of entity information 
    """
    wksp_name, wksp_ref = workspace
    global _rally_schema
    global _rally_entity_cache

    _rally_schema[wksp_ref] = {}

    for ix, raw_item_info in enumerate(schema_info):
        item = SchemaItem(raw_item_info)
        _rally_schema[wksp_ref][item.ElementName] = item
        if item.Abstract:
            continue
        if  item.ElementName not in _rally_entity_cache:
            _rally_entity_cache[item.ElementName] = item.ElementName
        if item.TypePath != item.ElementName:
            _rally_schema[wksp_ref][item.TypePath] = item
            if item.TypePath not in _rally_entity_cache:
                _rally_entity_cache[item.TypePath] = item.TypePath
    _rally_schema[wksp_ref]['Story']     = _rally_schema[wksp_ref]['HierarchicalRequirement']
    _rally_schema[wksp_ref]['UserStory'] = _rally_schema[wksp_ref]['HierarchicalRequirement']

    unaccounted_for_entities = [entity_name for entity_name in list(_rally_schema[wksp_ref].keys())
                                             if  entity_name not in classFor
                                             and not entity_name.startswith('ObjectAttr')
                               ]
    for entity_name in unaccounted_for_entities:
        if entity_name in ['ScopedAttributeDefinition']:
            continue
                           
        entity = _rally_schema[wksp_ref][entity_name]
        typePath = entity.TypePath
        pyralized_class_name = str(typePath.replace('/', '_'))
        if pyralized_class_name not in classFor:
            parentClass = WorkspaceDomainObject
            if entity.Parent:
                try:
                    parentClass = classFor[entity.Parent]
                except:
                    pass
            rally_entity_class = _createClass(pyralized_class_name, parentClass)
            classFor[typePath] = rally_entity_class


def getSchemaItem(workspace, entity_name):
    wksp_name, wksp_ref = workspace
    global _rally_schema
    if wksp_ref not in _rally_schema:
        raise Exception("Fault: no _rally_schema info for %s" % wksp_ref)
    schema = _rally_schema[wksp_ref]
    if entity_name not in schema:
        return None
    return schema[entity_name]


def _createClass(name, parentClass):
    """
        Dynamically create a class named for name whose parent is parent, and
        make the newly created class available by name in the global namespace.
    """
    rally_entity_class = type(name, (parentClass,), {})
    
    globals()[name] = rally_entity_class
    return rally_entity_class


__all__ = [processSchemaInfo, classFor, validRallyType, getSchemaItem,
           InvalidRallyTypeNameError, UnrecognizedAllowedValuesReference,
           PORTFOLIO_ITEM_SUB_TYPES
          ]
