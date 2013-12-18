
###################################################################################################
#
#  pyral.restapi - Python Rally REST API module
#          round 10 version with better RallyQueryBuilder
#          notable dependencies:
#               requests v2.x or greater now recommended
#                  must use Python 2.6, 2.7 now with requests >= 2.x
#
###################################################################################################

__version__ = (0, 9, 4)

import sys, os
import re
import types
import time
import urllib
import json
import string
import base64
from operator import itemgetter, attrgetter
import logging
import copy

import requests   

# intra-package imports
from .config  import PROTOCOL, SERVER, WS_API_VERSION, WEB_SERVICE, RALLY_REST_HEADERS
from .config  import USER_NAME, PASSWORD 
from .config  import PAGESIZE, START_INDEX, MAX_ITEMS
from .config  import timestamp

###################################################################################################

CONJUNCTION_PATT = re.compile(' (AND|OR) ', re.I) # to allow 'and', 'or', 'AND', 'OR'

# 
# define a module global that should be set up/known before a few more module imports
#
_rallyCache = {}  # keyed by a context tuple (server, user, password, workspace, project)
                  # value is a dict with at least:
                  # a key of 'rally'    whose value there is a Rally instance  and
                  # a key of 'hydrator' whose value there is an EntityHydrator instance

#
# another module global for TypeDefinition info
#  it's intended to be able to access a TypeDefinition.ref , .ElementName, and .Name attrs only
#
_type_definition_cache = {} # keyed by a type of context info and type definition ElementName
                            # value is a minimally hydrated TypeDefinition instance

#
# Yo! another module global here...
#
_allowedValueAlias = {}  # a dict keyed by entity name
                         # Project|Release|Iteration : { OID: Name value, ... }
                         # User & Owner are conspicuously not covered...

warning = sys.stderr.write

SERVICE_REQUEST_TIMEOUT = 120

###################################################################################################

class RallyRESTAPIError(Exception): pass

#
# define a couple of entry point functions for use by other pkg modules and import the modules
#
def hydrateAnInstance(context, item, existingInstance=None):
    global _rallyCache
    rallyContext = _rallyCache.get(context, None)
    if not rallyContext:
        # throwing an Exception is probably the correct thing to do
        return None
    hydrator = rallyContext.get('hydrator', None)
    if not hydrator:
        hydrator = EntityHydrator(context, hydration="full")
        rallyContext['hydrator'] = hydrator
    return hydrator.hydrateInstance(item, existingInstance=existingInstance)

def getResourceByOID(context, entity, oid, **kwargs):
    """
        Retrieves a reference in _rallyCache to a Rally instance and uses that to 
        call its internal _getResourceByOID method
        Returns a RallyRESTResponse instance 
        that has status_code, headers and content attributes.
    """
##
##    print "getResourceByOID called:"
##    print "   context: %s" % context
##    print "    entity: %s" % entity
##    print "       oid: %s" % oid
##    print "    kwargs: %s" % kwargs
##    sys.stdout.flush()
##
##    if entity == 'context':
##        raise Exception("getResourceByOID called to get resource for entity of 'context'")
##
    global _rallyCache
    rallyContext = _rallyCache.get(context, None)
    if not rallyContext:
        # raising an Exception is the only thing we can do, don't see any prospect of recovery...
        raise RallyRESTAPIError('Unable to find Rally instance for context: %s' % context)

       # print "_rallyCache.keys:"
       # for key in _rallyCache.keys():
       #     print "    -->%s<--" % key
       # print ""
       # print " apparently no key to match: -->%s<--" % context
       # print " context is a %s" % type(context)

       

    rally = rallyContext.get('rally')
    resp = rally._getResourceByOID(context, entity, oid, **kwargs)
    if 'unwrap' not in kwargs or not kwargs.get('unwrap', False):
        return resp
    response = RallyRESTResponse(rally.session, context, "%s.x" % entity, resp, "full", 1)
    return response


#  these imports have to take place after the prior class and function defs 
from .rallyresp import RallyRESTResponse, ErrorResponse
from .hydrate   import EntityHydrator
from .context   import RallyContext, RallyContextHelper
from .entity    import validRallyType
from .query_builder import RallyUrlBuilder

__all__ = ["Rally", "getResourceByOID", "hydrateAnInstance", "RallyUrlBuilder"]


def _createShellInstance(context, entity_name, item_name, item_ref):
    if item_ref.endswith('.js'):
        oid = item_ref[:-3].split('/').pop()
    else:
        oid = item_ref.split('/').pop()
    item = {
            'ObjectID' : oid, 
            'Name'     : item_name, 
            '_type'    : entity_name,
            '_ref'     : item_ref, 
            'ref'      : '%s/%s' % (entity_name.lower(), oid)
           }
    hydrator = EntityHydrator(context, hydration="shell")
    return hydrator.hydrateInstance(item)
        
##################################################################################################

class Rally(object):
    """
        An instance of this class provides the instance holder the ability to 
        interact with Rally via the Rally REST WSAPI.
        The holder can create, query (read), update and delete Rally entities 
        (but only selected appropriate entities).
        In addition, there are several convenience methods (for users, workspaces and projects)
        that allow the holder to quickly get a picture of their Rally operating environment.
    """
    ARTIFACT_TYPE = { 'S' : 'Story', 
                     'US' : 'Story', 
                     'DE' : 'Defect',
                     'DS' : 'DefectSuite',
                     'TA' : 'Task',
                     'TC' : 'TestCase',
                     'TS' : 'TestSet',
                     'PI' : 'PortfolioItem'
                    }
    FORMATTED_ID_PATTERN = re.compile(r'^[A-Z]{1,2}\d+$')
                                      #S|US|DE|DS|TA|TC|TS|PI
    MAX_ATTACHMENT_SIZE = 5000000  # approx 5MB 


    def __init__(self, server=SERVER, user=USER_NAME, password=PASSWORD, 
                       version=WS_API_VERSION, warn=True, **kwargs):
        self.server    = server
        self.user      = user
        self.password  = password
        self.version   = version
        self._inflated = False
        self.service_url = "%s://%s/%s" % (PROTOCOL, self.server, WEB_SERVICE % self.version)
        self.hydration   = "full"
        
        # set up logging
        self._log=logging.getLogger('restapi.Rally')
        self._logAttrGet = logging.getLogger('restapi.Rally.AttrGet')
        self._log.info("Following entries record Rally REST API interaction via %s for user: %s'", self.service_url, self.user)
        
        config = {}
        if kwargs and 'debug' in kwargs and kwargs.get('debug', False):
            config['verbose'] = sys.stdout

        credentials = requests.auth.HTTPBasicAuth(self.user, self.password)
        proxy_dict = {} 
        https_proxy = os.environ.get('HTTPS_PROXY', None) or os.environ.get('https_proxy', None)
        if https_proxy and https_proxy not in ["", None]:
            if not https_proxy.startswith('http'):
                https_proxy = "http://%s" % https_proxy # prepend the standard http scheme on the front-end
                os.environ['https_proxy'] = https_proxy
                os.environ['HTTPS_PROXY'] = https_proxy
            proxy_dict['https'] = https_proxy

        verify_ssl_cert = True
        if kwargs and 'verify_ssl_cert' in kwargs:
            vsc = kwargs.get('verify_ssl_cert')
            if vsc in [False, True]:
                verify_ssl_cert = vsc

        requests_version_major = int(requests.__version__.split('.').pop(0))
        if requests_version_major == 0: # requests 0.x.y syntax for getting a session
            self.session = requests.session(headers=RALLY_REST_HEADERS, auth=credentials,
                                            timeout=10.0, proxies=proxy_dict, 
                                            verify=verify_ssl_cert, config=config)
        else:  # requests 1.x and greater syntax for getting a session
            self.session = requests.Session()
            self.session.headers = RALLY_REST_HEADERS
            self.session.auth = credentials
            self.session.timeout = 10.0
            self.session.proxies = proxy_dict
            self.session.verify = verify_ssl_cert
            self.session.config = config
        
        self.contextHelper = RallyContextHelper(self, server, user, password)
        self.contextHelper.check(self.server)

        global _rallyCache
        if self.contextHelper.currentContext() not in _rallyCache:
            _rallyCache[self.contextHelper.currentContext()] = {'rally' : self}

        if self.contextHelper.defaultContext not in _rallyCache:
            _rallyCache[self.contextHelper.defaultContext]   = {'rally' : self}

        __adjust_cache = False

        if 'workspace' in kwargs and kwargs['workspace'] != self.contextHelper.currentContext().workspace \
           and kwargs['workspace'] != 'default':
            if self.contextHelper.isAccessibleWorkspaceName(kwargs['workspace']):
                self.contextHelper.setWorkspace(kwargs['workspace'])
                __adjust_cache = True
            else:
                 warning("WARNING: Unable to use your workspace specification, that value is not listed in your subscription\n")
                  
        if 'project' in kwargs and kwargs['project'] != self.contextHelper.currentContext().project \
           and kwargs['project'] != 'default':
            accessibleProjects = [name for name, ref in self.contextHelper.getAccessibleProjects(workspace='current')]

            if kwargs['project'] in accessibleProjects:
                self.contextHelper.setProject(kwargs['project'])
                __adjust_cache = True
            else:
                issue = ("Unable to use your project specification of '%s', " 
                         "that value is not associated with current workspace setting of: '%s'" )
                raise Exception(issue % (kwargs['project'], self.contextHelper.currentContext().workspace))

        if 'project' not in kwargs:
            #
            # It's possible that the invoker has specified a workspace but no project 
            # and the default project isn't in the workspace that was specified.
            # In that case reset the current and default project to first project in 
            # the list of projects for the current workspace.
            #
            cdp = self.contextHelper.getProject()          # cdp  alias for current_default_project
            ndp = self.contextHelper.resetDefaultProject() # ndp  alias for new_default_project
            if ndp != cdp:  # have to test both the name and ref values!!
                __adjust_cache = True
                cdp_name, cdp_ref = cdp
                ndp_name, ndp_ref = ndp
                # but we'll only issue a warning if the project names are different
                if self.warningsEnabled() and ndp_name != cdp_name:
                    prob = "WARNING: Default project changed to '%s' (%s).\n" + \
                           "         Your normal default project: '%s' is not valid for\n" +\
                           "         the current workspace setting of: '%s'\n"
                    short_proj_ref = "/".join(ndp_ref.split('/')[-2:])[:-3]
                    wksp_name, wksp_ref = self.contextHelper.getWorkspace()
                    warning(prob % (ndp_name, short_proj_ref, cdp_name, wksp_name))

        if __adjust_cache:
            _rallyCache[self.contextHelper.currentContext()] = {'rally' : self}

    def __getstate__(self):
        """
            Preserve the current state of the rally connection, sans the loggers
            for pickle support
        """
        ret=copy.copy(self.__dict__)
        del ret['_log']
        del ret['_logAttrGet']
        return (ret)

    def __setstate__(self,state):
        """
            Restore the current state for pickle support. Including re-creating
            the loggers and adding the contexts back into the cache, if neccessary
        """
        self.__dict__=state
        self._log=logging.getLogger('restapi.Rally')
        self._logAttrGet = logging.getLogger('restapi.Rally.AttrGet')

        global _rallyCache
        if self.contextHelper.currentContext() not in _rallyCache:
            _rallyCache[self.contextHelper.currentContext()] = {'rally' : self}

        if self.contextHelper.defaultContext not in _rallyCache:
            _rallyCache[self.contextHelper.defaultContext]   = {'rally' : self}

    def _wpCacheStatus(self):
        """
            intended to be only for unit testing...
              values could be None, True, False, 'minimal', 'narrow', 'wide'
        """
        return self.contextHelper._inflated


    def serviceURL(self):
        """
            Crutch to allow the RallyContextHelper to pass this along in the initialization
            of a RallyContext instance.
        """
        return self.service_url

    def enableLogging(self, *args, **kwargs):
        ''' enableLogging - now a noop, because logging is configured through
            python logging API
        '''
        pass


    def disableLogging(self):
        ''' disableLogging - now a noop, because logging is configured through
            python logging API
        '''
        pass

    def enableWarnings(self):
        ''' enableWarnings - now a noop, because logging is configured through
            python logging API
        '''
        pass

    def disableWarnings(self):
        ''' disableWarnings - now a noop, because logging is configured through
            python logging API
        '''
        pass

    def warningsEnabled(self):
        return self._log.getEffectiveLevel()<=logging.WARNING

    def subscriptionName(self):
        """
            Returns the name of the subscription in the currently active context.
        """
        return self.contextHelper.currentContext().subscription()

    def setWorkspace(self, workspaceName):
        """
            Given a workspaceName, set that as the currentWorkspace and use the ref for 
            that workspace in subsequent interactions with Rally.
        """
        if not self.contextHelper.isAccessibleWorkspaceName(workspaceName):
            raise Exception('Specified workspace not valid for your credentials')
        self.contextHelper.setWorkspace(workspaceName)
##
##        print self.contextHelper.currentContext()
##

    def getWorkspace(self):
        """
            Returns a minimally hydrated Workspace instance with the Name and ref
            of the workspace in the currently active context.
        """
        context = self.contextHelper.currentContext()
        wksp_name, wksp_ref = self.contextHelper.getWorkspace()
        return _createShellInstance(context, 'Workspace', wksp_name, wksp_ref)

    def getWorkspaces(self):
        """
            Return a list of minimally hydrated Workspace instances
            that are available to the registered user in the currently active context.

            Return a list of (workspace.Name, workspace._ref) tuples
            that are available to the registered user in the currently active context.
        """
        context = self.contextHelper.currentContext()
        wkspcs  = self.contextHelper.getAccessibleWorkspaces()
        workspaces = [_createShellInstance(context, 'Workspace', wksp_name, wksp_ref)
                      for wksp_name, wksp_ref in sorted(wkspcs)
                     ]
        return workspaces


    def setProject(self, projectName):
        """
            Given a projectName, set that as the current project and use the ref for 
            that project in subsequent interractions with Rally.
        """
        eligible_projects = [proj for proj,ref in self.contextHelper.getAccessibleProjects(workspace='current')]
        if projectName not in eligible_projects:
            raise Exception('Specified project not valid for your current workspace or credentials')
        self.contextHelper.setProject(projectName)


    def getProject(self, name=None):
        """
            Returns a minimally hydrated Project instance with the Name and ref
            of the project in the currently active context if the name keyword arg
            is not supplied or the Name and ref of the project identified by the name
            as long as the name identifies a valid project in the currently selected workspace.
            Returns None if a name parameter is supplied that does not identify a valid project
            in the currently selected workspace.
        """
        context = self.contextHelper.currentContext()
        if not name:
            proj_name, proj_ref = self.contextHelper.getProject()
            return _createShellInstance(context, 'Project', proj_name, proj_ref)
        projs = self.contextHelper.getAccessibleProjects(workspace='current')
        hits = [(proj,ref) for proj,ref in projs if str(proj) == str(name)]
        if not hits:
            return None
        return _createShellInstance(context, 'Project', name, hits[0][1])
        

    def getProjects(self, workspace=None):
        """
            Return a list of minimally hydrated Project instances
            that are available to the registered user in the currently active context.
        """
        wksp_target = workspace or 'current'
        projs = self.contextHelper.getAccessibleProjects(workspace=wksp_target)
        context = self.contextHelper.currentContext()
        projects = [_createShellInstance(context, 'Project', proj_name, proj_ref)
                      for proj_name, proj_ref in sorted(projs)
                   ]
        return projects


    def getUserInfo(self, oid=None, username=None, name=None):
        """
            A convenience method to collect specific user related information.
            Caller must provide at least one keyword arg and non-None / non-empty value
            to identify the user target on which to obtain information.
            The name     keyword arg is associated with the User.DisplayName attribute
            The username keyword arg is associated with the User.UserName attribute
            If provided, the oid keyword argument is used, even if other keyword args are 
            provided. Similarly, if the username keyword arg is provided it is used
            even if the name keyword argument is provided.
            User
                DisplayName
                UserName
                Disabled
                EmailAddress
                FirstName
                MiddleName
                LastName
                OnpremLdapUsername
                ShortDisplayName
                Role
                TeamMemberships (from projects)
                LastPasswordUpdateDate
                UserPermissions - from UserPermission items associated with this User

            UserProfile
                DefaultWorkspace
                DefaultProject
                TimeZone
                DateFormat
                DateTimeFormat
                EmailNotificationEnabled
                SessionTimeoutSeconds
                SessionTimeoutWarning

            UserPermission
                Name  - name of the User Permission
                Role

            Returns either a single User instance or a list of User instances                
                
        """
        context  = self.contextHelper.currentContext()
        item, response = None, None
        if oid:
            item = self._itemQuery('User', oid)
        elif username:
            response = self.get('User', fetch=True, query='UserName = "%s"' % username)
        elif name:
            response = self.get('User', fetch=True, query='DisplayName = "%s"' % name)
        else:
            raise RallyRESTAPIError("No specification provided to obtain User information")

        if item: 
            return item
        if response: 
            return [user for user in response]
        return None


    def getAllUsers(self, workspace=None):
        """
            Given that actually getting full information about all users in the workspace
            via the Rally WSAPI is somewhat opaque, this method offers a one-stop convenient
            means of obtaining usable information about users in the named workspace.
            If no workspace is specified, then the current context's workspace is used.

            Return a list of User instances (fully hydrated for scalar attributes)
            whose ref and collection attributes will be lazy eval'ed upon access.
        """
        saved_workspace_name, saved_workspace_ref = self.contextHelper.getWorkspace()
        if not workspace:
            workspace = saved_workspace_name
        self.setWorkspace(workspace)

        context, augments = self.contextHelper.identifyContext(workspace=workspace)
        workspace_ref = self.contextHelper.currentWorkspaceRef()

        # Somewhere post 1.3x in Rally WSAPI, the ability to list the User attrs along with the TimeZone
        # attr of UserProfile and have that all returned in 1 query was no longer supported.
        # So we do a full bucket query on User and UserProfile separately and "join" them via our
        # own brute force method so that the the caller can access any UserProfile attribute
        # for a User.
        user_attrs = ["Name", "UserName", "DisplayName", 
                      "FirstName", "LastName", "MiddleName",
                      "ShortDisplayName", "OnpremLdapUsername",
                      "CreationDate", "EmailAddress",
                      "LastPasswordUpdateDate", "Disabled",
                      "Subscription", "SubscriptionAdmin",
                      "Role", "UserPermissions", "TeamMemberships", 
                      "UserProfile", 
                      "TimeZone",            # a UserProfile attribute
                      # and other UserProfile attributes
                     ]

        users_resource = 'users.js?fetch=true&query=&pagesize=200&start=1&workspace=%s' % (workspace_ref)
        full_resource_url = '%s/%s' % (self.service_url, users_resource)
        response = self.session.get(full_resource_url, timeout=SERVICE_REQUEST_TIMEOUT)
        if response.status_code != 200:
            return []
        response = RallyRESTResponse(self.session, context, users_resource, response, "full", 0)
        users = [user for user in response]

        user_profile_resource = 'userprofile.js?fetch=true&query=&pagesize=200&start=1&workspace=%s' % (workspace_ref)
        response = self.session.get('%s/%s' % (self.service_url, user_profile_resource), 
                                    timeout=SERVICE_REQUEST_TIMEOUT)
        if response.status_code != 200:
            warning("WARNING: Unable to retrieve UserProfile information for users\n")
            profiles = []
        else:
            response = RallyRESTResponse(self.session, context, user_profile_resource, response, "full", 0)

            profiles = [prof for prof in response]

        # do our own brute force "join" operation on User to UserProfile info 
        for user in users:
            # get any matching user profiles (aka mups), there really should only be 1 matching...
            mups = [prof for prof in profiles 
                          if prof._ref == user.UserProfile._ref] 
            if not mups:
                problem = "unable to find a matching UserProfile record for User: %s  UserProfile: %s"
                warning("WARNING: %s\n" % (problem % (user.DisplayName, user.UserProfile)))
                continue
            else:
                if len(mups) > 1:
                    anomaly = "Found %d UserProfile items associated with username: %s"
                    warning("WARNING: %s\n" % (anomaly % (len(mups), user.UserName)))
                # now attach the first matching UserProfile to the User
                user.UserProfile = mups[0]
            
        self.setWorkspace(saved_workspace_name)
        return users


    def _officialRallyEntityName(self, supplied_name):
        if supplied_name in ['Story', 'UserStory', 'User Story']:
            supplied_name = 'HierarchicalRequirement'

        # here's where we'd make an inquiry into entity to see if the supplied_name
        # is a Rally entity on which CRUD ops are permissible.
        # An Exception is raised if not.
        # If supplied_name resolves in some way to a valid Rally entity,
        # this returns either a simple name or a TypePath string (like PortfolioItem/Feature)
        official_name = validRallyType(self, supplied_name)
        return official_name


    def _getResourceByOID(self, context, entity, oid, **kwargs):
        """
            The _ref URL (containing the entity name and OID) can be used unchanged but the format 
            of the response is slightly different from that returned when the resource URL is 
            constructed per spec (by this class's get method).  The _ref URL response can be 
            termed "un-wrapped" in that there's no boilerplate involved, just the JSON object.
            Returns a raw response instance (with status_code, headers and content attributes).
        """
##
##        print "in _getResourceByOID, OID specific resource ...", entity, oid
##        sys.stdout.flush()
##
        resource = '%s/%s' % (entity, oid)
        if not resource.endswith('.js'):
            resource += '.js'
        if '_disableAugments' not in kwargs:
            contextDict = context.asDict()
##
##            print "_getResourceByOID, current contextDict: %s" % repr(contextDict)
##            sys.stdout.flush()
##
            context, augments = self.contextHelper.identifyContext(**contextDict)
            if augments:
                resource += ("?" + "&".join(augments))
##
##            print "_getResourceByOID, modified contextDict: %s" % repr(context.asDict())
##            sys.stdout.flush()
##
        full_resource_url = "%s/%s" % (self.service_url, resource)
        self._logAttrGet.debug("Attribute-GET %s",resource)
##
##        print "issuing GET for resource: %s" % full_resource_url
##        sys.stdout.flush()
##
        try:
            raw_response = self.session.get(full_resource_url)
        except Exception as ex:
            exctype, value, tb = sys.exc_info()
            warning('%s: %s\n' % (exctype, value)) 
            return None
##
##        print raw_response: %s" % raw_response
##        sys.stdout.flush()
##
        return raw_response


    def _itemQuery(self, entityName, oid, workspace=None, project=None):
        """
            Internal method to retrieve a specific instance of an entity identified by the OID.
        """
##
##        print "Rally._itemQuery('%s', %s, workspace=%s, project=%s)" % (entityName, oid, workspace, project)
##
        resource = '%s/%s' % (entityName, oid)
        context, augments = self.contextHelper.identifyContext(workspace=workspace, project=project)
        if augments:
            resource += ("?" + "&".join(augments))
        self._log.debug("GET %s",resource)
        response = self._getResourceByOID(context, entityName, oid)
        self._log.debug(" ->%s %s",response.status_code, resource)
        if not response or response.status_code != 200:
            problem = "Unreferenceable %s OID: %s" % (entityName, oid)
            raise RallyRESTAPIError('%s %s' % (response.status_code, problem))

        response = RallyRESTResponse(self.session, context, '%s.x' % entityName, response, "full", 1)
        item = response.next()
        return item    # return back an instance representing the item


    def _greased(self, item_data):
        """
            Given a dict instance with keys that are attribute names for some
            Rally entity associated with values that are to be created for
            or updated in a target Rally entity, identify which attributes are 
            likely COLLECTION types and perform any transformation necessary to 
            ensure that the prospective attribute values are refs that are placed 
            in a dict and thence put in a list of values for the attribute.
            As an initial implementation to forego yet another round trip query
            to Rally for all the Attributes on an entity name, we employ
            the following rough heuristic to determine what attributes 
            are COLLECTIONS and thus _may_ need greasing:
               Attribute name of Children or an attribute that ends in 's'.
            So, we'll look at the keys in item_data that match our heuristic
            (case-insensitive) and then we also check to see if the value 
            associated with the attribute name key is a list.
            If there are no hits for those criteria, return the item_data untouched.
            Otherwise, roll thru the attribute name hits whose value is a list
            and determine if each element in the list is a string that has the 
            pattern of "someentityname/324324", (where the digits are an OID value)
            and if so, replace the element value with a dict with a key of "_ref"
            whose value is the original list element.
            Return the item_dict with any updates to COLLECTIONS attributes that
            needed "greasing".
        """
        collection_attributes = [attr_name for attr_name in item_data.keys()
                                            if attr_name.lower == 'children'
                                            or attr_name[-1] == 's'
                                ]
        if not collection_attributes:
            return item_data
        for attr_name in collection_attributes:
            if type(item_data[attr_name]) != types.ListType:
                continue
            obj_list = []
            for value in item_data[attr_name]:
                # is value like "someentityname/34223214" ?
                if type(value) == types.StringType and '/' in value \
                and re.match('^\d+$', value.split('/')[-1]):
                    obj_list.append({"_ref" : value})  # transform to a dict instance
                else:
                    obj_list.append(value)   # value is untouched
            item_data[attr_name] = obj_list
        return item_data


    def get(self, entity, fetch=False, query=None, order=None, **kwargs):
        """
            A REST approach has the world seen as resources with the big 4 ops available on them
            (GET, PUT, POST, DELETE). There are other ops but we don't care about them here.
            Each resource _should_ have a unique URI that is used to identify the resource.
            The GET operation is used to specify that we want a representation of that resource.
            For Rally, in order to construct a URI, we need the name of the entity, the attributes
            of the entity (and attributes on any child/parent entity related to the named entity),
            the query (selection criteria) and the order in which the results should be returned.

            The fetch argument (boolean or a comma separated list of attributes) indicates whether 
            we get complete representations of objects back or whether we get "shell" objects with 
            refs to be able to retrieve the full info at some later time.

            An optional instance=True keyword argument will result in returning an instantiated 
            Rally Entity if and only if the resultCount of the get is exactly equal to 1.
            Otherwise, a RallyRESTResponse instance is returned.

            All optional keyword args:
                fetch=True/False or "List,Of,Attributes,We,Are,Interested,In"
                query='FieldName = "some value"' or ['fld1 = 19', 'fld27 != "Shamu"', etc.]
                order="fieldName ASC|DESC"
                instance=False/True
                pagesize=n
                start=n
                limit=n
                projectScopeUp=True/False
                projectScopeDown=True/False
        """
        # TODO: this method too long, break into small setup, 2 or 3 subcalls and some wrapup
        # set some useful defaults...
        pagesize   = PAGESIZE
        startIndex = START_INDEX
        limit      = MAX_ITEMS

        if kwargs and 'pagesize' in kwargs:
            pagesize = kwargs['pagesize']

        if kwargs and 'start' in kwargs:
            try:
                usi = int(kwargs['start'])  # usi - user supplied start index
                if 0 < usi < MAX_ITEMS:     # start index must be greater than 0 and less than max
                    startIndex = usi
            except ValueError as ex: 
                pass

        if kwargs and 'limit' in kwargs:
            try:
                ulimit = int(kwargs['limit'])  # in case someone specifies something like limit=gazillionish
                limit = min(ulimit, MAX_ITEMS)
            except:
                pass

        if fetch == True:
            fetch = 'true'
            self.hydration = "full"
        elif fetch == False:
            fetch = 'false'
            self.hydration = "shell"
        elif type(fetch) == types.StringType and fetch.lower() != 'false':
            self.hydration = "full"
        elif type(fetch) in [types.ListType, types.TupleType]:
            fetch = ",".join(fetch)
            self.hydration = "full"

        entity = self._officialRallyEntityName(entity)
        resource = RallyUrlBuilder(entity)
        resource.qualify(fetch, query, order, pagesize, startIndex)

        if '_disableAugments' in kwargs:
            context = RallyContext(self.server, self.user, self.password, self.service_url)
        else:
            context, augments = self.contextHelper.identifyContext(**kwargs)
            workspace_ref = self.contextHelper.currentWorkspaceRef()
            project_ref   = self.contextHelper.currentProjectRef()
##
##            print "   workspace_ref: %s"   % workspace_ref
##            print "     project_ref:   %s" %   project_ref
##
            if workspace_ref:   # TODO: would we ever _not_ have a workspace_ref?
                if 'workspace' not in kwargs or ('workspace' in kwargs and kwargs['workspace'] is not None):
                    resource.augmentWorkspace(augments, workspace_ref)
                    if project_ref:
                        if 'project' not in kwargs or ('project' in kwargs and kwargs['project'] is not None):
                            resource.augmentProject(augments, project_ref)
                            resource.augmentScoping(augments)
        resource = resource.build()  # can also use resource = resource.build(pretty=True)
        full_resource_url = "%s/%s" % (self.service_url, resource)

        # TODO: see if much of above can be pushed into another method

        self._log.debug("GET %s",resource)

        response = None  # in case an exception gets raised in the session.get call ...
        try:
            # a response has status_code, content and data attributes
            # the data attribute is a dict that has a single entry for the key 'QueryResult' 
            # or 'OperationResult' whose value is in turn a dict with values of 
            # 'Errors', 'Warnings', 'Results'
            response = self.session.get(full_resource_url, timeout=SERVICE_REQUEST_TIMEOUT)
        except Exception as ex:
            if response:
##
##                print "Exception detected for session.get requests, response status code: %s" % response.status_code
##
                ret_code, content = response.status_code, response.content
            else:
                ret_code, content = 404, str(ex.args[0])
            self._log.debug("  -> %s", ret_code)
            errorResponse = ErrorResponse(ret_code, content)
            response = RallyRESTResponse(self.session, context, resource, errorResponse, self.hydration, 0)
            return response
##
##        print "response.status_code is %s" % response.status_code
##
        if response.status_code != 200:
            self._log.debug("Response code: %s",response.status_code)
##
##            print response
##
            #if response.status_code == 404:
            #    problem = "%s Service unavailable from %s, check for proper hostname" % (response.status_code, self.service_url)
            #    raise Exception(problem)
            errorResponse = ErrorResponse(response.status_code, response.content)
            response = RallyRESTResponse(self.session, context, resource, errorResponse, self.hydration, 0)
            return response

        response = RallyRESTResponse(self.session, context, resource, response, self.hydration, limit)
        if response.status_code == 200:
            desc = '%s TotalResultCount %s' % (entity, response.resultCount)
        else:
            desc = response.errors[0]
        self._log.debug("%s %s",response.status_code, desc)
        if kwargs and 'instance' in kwargs and kwargs['instance'] == True and response.resultCount == 1:
            return response.next()
        return response

    find = get # offer interface approximately matching Ruby Rally REST API, App SDK Javascript RallyDataSource


    def put(self, entityName, itemData, workspace='current', project='current', **kwargs):
        """
            Given a Rally entityName, a dict with data that the newly created entity should contain,
            issue the REST call and return the newly created target entity item.
        """
        # see if we need to transform workspace / project values of 'current' to actual
        if workspace == 'current':
            workspace = self.getWorkspace().Name  # just need the Name here
        if project == 'current':
            project = self.getProject().Name  # just need the Name here

        entityName = self._officialRallyEntityName(entityName)

        resource = "%s/create.js" % entityName.lower()
        context, augments = self.contextHelper.identifyContext(workspace=workspace, project=project)
        if augments:
            resource += ("?" + "&".join(augments))
        full_resource_url = "%s/%s" % (self.service_url, resource)

        item = {entityName: self._greased(itemData)} # where _greased is a convenience
                                                     # method that will transform
                                                     # any ref lists for COLLECTION attributes
                                                     # into a list of one-key dicts {'_ref' : ref}
        payload = json.dumps(item)
        self._log.debug("PUT %s\n%27.27s %s",resource, " ", payload)
        response = self.session.put(full_resource_url, data=payload, headers=RALLY_REST_HEADERS)
        response = RallyRESTResponse(self.session, context, resource, response, "shell", 0)
        if response.status_code != 200:
            desc = response.errors[0]
            self._log.debug("%s %s",response.status_code, desc)
            raise RallyRESTAPIError('%s %s' % (response.status_code, desc))

        item = response.content[u'CreateResult'][u'Object']
        ref  = str(item[u'_ref'])
        item_oid = int(ref.split('/')[-1][:-3])
        desc = "created %s OID: %s" % (entityName, item_oid)
        self._log.debug("%s %s",response.status_code, desc)

        # now issue a request to get the entity item (mostly so we can get the FormattedID)
        # and return it
        item = self._itemQuery(entityName, item_oid, workspace=workspace, project=project)
        return item
        
    create = put  # a more intuitive alias for the operation


    def post(self, entityName, itemData, workspace='current', project='current', **kwargs):
        """
            Given a Rally entityName, a dict with data that the entity should be updated with,
            issue the REST call and return a representation of updated target entity item.
        """
        # see if we need to transform workspace / project values of 'current' to actual
        if workspace == 'current':
            workspace = self.getWorkspace().Name  # just need the Name here
        if project == 'current':
            project = self.getProject().Name  # just need the Name here

        entityName = self._officialRallyEntityName(entityName)

        oid = itemData.get('ObjectID', None)
        if not oid:
            formattedID = itemData.get('FormattedID', None)
            if not formattedID:
                raise RallyRESTAPIError('An identifying field (Object or FormattedID) must be specified')
            fmtIdQuery = 'FormattedID = "%s"' % formattedID
            response = self.get(entityName, fetch="ObjectID", query=fmtIdQuery, 
                                workspace=workspace, project=project)
            if response.status_code != 200 or response.resultCount == 0:
                raise RallyRESTAPIError('Target %s %s could not be located' % (entityName, formattedID))
                
            target = response.next()
            oid = target.ObjectID
##
##            print "target OID: %s" % oid
##
            itemData['ObjectID'] = oid

        resource = '%s/%s.js' % (entityName.lower(), oid) 
        context, augments = self.contextHelper.identifyContext(workspace=workspace, project=project)
        if augments:
            resource += ("?" + "&".join(augments))
        full_resource_url = "%s/%s" % (self.service_url, resource)
##
##        print "resource: %s" % resource
##
        item = {entityName: self._greased(itemData)}
        payload = json.dumps(item)
        self._log.debug("POST %s\n%27.27s %s",resource, " ", item)
        response = self.session.post(full_resource_url, data=payload, headers=RALLY_REST_HEADERS)
        response = RallyRESTResponse(self.session, context, resource, response, "shell", 0)
        if response.status_code != 200:
            raise RallyRESTAPIError('Unable to update the %s' % entityName)

        # now issue a request to get the entity item (mostly so we can get the FormattedID)
        # and return it
        item = self._itemQuery(entityName, oid, workspace=workspace, project=project)
        return item

    update = post  # a more intuitive alias for the operation


    def delete(self, entityName, itemIdent, workspace='current', project='current', **kwargs):
        """
            Given a Rally entityName, an identification of a specific Rally instnace of that 
            entity (in either OID or FormattedID format), issue the REST DELETE call and 
            return an indication of whether the delete operation was successful.
        """
        # see if we need to transform workspace / project values of 'current' to actual
        if workspace == 'current':
            workspace = self.getWorkspace().Name  # just need the Name here
        if project == 'current':
            project = self.getProject().Name  # just need the Name here

        entityName = self._officialRallyEntityName(entityName)

        # guess at whether itemIdent is an ObjectID or FormattedID via 
        # regex matching (all digits or 1-2 upcase chars + digits)
        objectID = itemIdent  # at first assume itemIdent is the ObjectID
        if re.match('^[A-Z]{1,2}\d+$', itemIdent):
            fmtIdQuery = 'FormattedID = "%s"' % itemIdent
            response = self.get(entityName, fetch="ObjectID", query=fmtIdQuery, 
                                workspace=workspace, project=project)
            if response.status_code != 200:
                raise RallyRESTAPIError('Target %s %s could not be located' % (entityName, itemIdent))
                
            target = response.next()
            objectID = target.ObjectID
##
##            if kwargs.get('debug', False):
##               print "DEBUG: target OID -> %s" % objectID
##
        resource = "%s/%s.js" % (entityName.lower(), objectID)
        context, augments = self.contextHelper.identifyContext(workspace=workspace, project=project)
        if augments:
            resource += ("?" + "&".join(augments))
        full_resource_url = "%s/%s" % (self.service_url, resource)
        self._log.debug("DELETE %s",resource)
        response = self.session.delete(full_resource_url, headers=RALLY_REST_HEADERS)
        if response and response.status_code != 200:
            self._log.debug("%s %s ...",response.status_code, response.content[:56])
##
##            if kwargs.get('debug', False):
##                print response.status_code, response.headers, response.content
##
            errorResponse = ErrorResponse(response.status_code, response.content)
            response = RallyRESTResponse(self.session, context, resource, errorResponse, self.hydration, 0)
            problem = "ERRORS: %s\nWARNINGS: %s\n" % ("\n".join(response.errors), 
                                                      "\n".join(response.warnings))
            raise RallyRESTAPIError(problem)

##
##        print response.content
##
        response = RallyRESTResponse(self.session, context, resource, response, "shell", 0)
        if response.errors:
            status = False
            desc = response.errors[0]
        else:
            status = True
            desc = '%s deleted' % entityName
        self._log.debug("%s %s",response.status_code, desc)

        return status

    def typedef(self, target_type):
        """
            Given the name of a target Rally type definition return an instance 
            of a TypeDefinition class matching the target.  Cache the TypeDefinition
            for the context so that repeated calls to the same target_type only result
            in one call to Rally.
        """
        ctx  = self.contextHelper.currentContext()
        td_key = (ctx.server, ctx.subs_name, ctx.workspace, ctx.project, target_type)

        if td_key not in _type_definition_cache:
            td = self.get('TypeDefinition', fetch='ElementName,Name,Parent,TypePath')

            if not td:
                raise Exception("Unable to obtain Rally TypeDefinition information")

            tds = [item for item in td]
            if not tds:
                raise Exception("Invalid Rally entity name: %s" % target_type)

            for td in tds:
                type_name = '%s' % td.ElementName
                parent = td.Parent.ElementName
                if parent == "PortfolioItem":
                    type_name = "%s/%s" % (parent, td.ElementName)
                td_cache_key = (ctx.server, ctx.subs_name, ctx.workspace, ctx.project, type_name)
                _type_definition_cache[td_cache_key] = td

        if td_key in _type_definition_cache:
            return _type_definition_cache[td_key]
        alt_keys = [quint_key[-1] for quint_key in _type_definition_cache.keys if quint_key[-1] == target_type]
        if alt_keys and len(alt_keys) == 1: # good, there's only one possible match
            return _type_definition_cache[alt_keys[0]]

        return None

    def getState(self, entity, state_name):
        """
            State is now (Sep 2012) a Rally type (aka entity) not a String.
            In order to somewhat insulate pyral package users from the increased complexity 
            of that approach, this is a convenience method that given a target entity (like
            Defect, PortfolioItem/<subtype>, etc.) and a state name, an inquiry to the Rally
            system is executed and the matching entity is returned.

            WARNING:  This only works with PortfolioItem subclasses:
                       Theme, Initiative, Feature
        """
        criteria = [ 'TypeDef.Name = "%s"' % entity,
                     'Name = "%s"'         % state_name
                   ]

        state = self.get('State', fetch=True, query=criteria, project=None, instance=True)
        return state

    def getStates(self, entity):
        """
            This method must deal with essentially duplicated results as for whatever reason
            there can be multiple State items with the same OrderIndex, Name, Enabled, Accepted values
            but with differing ObjectID and CreationDate values.  We arbitrarily take the last State
            for each OrderIndex, Name pair and return the resulting list.
        """
        response = self.get('State', query='TypeDef.Name = "%s"' % entity, order="OrderIndex,ObjectID", project=None)
        state_ix = {}
        for state in [item for item in response]:
            state_ix[(state.OrderIndex, state.Name)] = state
        state_keys = sorted(state_ix.keys(), key=itemgetter(0))
        states = [state_ix[key] for key in state_keys]
        return states

    def allowedValueAlias(self, entity, refUrl):
        """
            Use the _allowedValueAlias as a cache. A cache hit results from 
            having an entity key in _allowedValueAlias AND and entry for the OID 
            contained in the refUrl, the return is the OID and the alias value.
            If there is no cache hit for the entity, issue a GET against
            self.service_url/<entity>.js?fetch=ObjectID,Name (or UserName,DisplayName)
        """
        urlFields = refUrl.split('/')
        oid = urlFields.pop()
        result = (oid, "--UNKNOWN OID--")
        actualEntity = urlFields.pop().lower()  # this may be different from entity, eg.
                                                # entity=SubmittedBy, actualEntity=User
        if actualEntity == 'user':    # special case processing for user follows...
            if actualEntity not in _allowedValueAlias:
                _allowedValueAlias[actualEntity] = {}
            cache = _allowedValueAlias[actualEntity]
            if oid in cache:
                result = (oid, cache[oid])
            else:
                item = self._itemQuery(actualEntity, oid)   # query against 'User' for item
                cache[oid] = (item.DisplayName, item.UserName)
                result = (oid, (item.DisplayName, item.UserName))
        else:   # normal case, entity == actualEntity (or at least no functional difference)
            hydrationSetting = self.hydration
            self.hydrate = "shell"

            if entity not in _allowedValueAlias:
                _allowedValueAlias[entity] = {}
            cache = _allowedValueAlias[entity]
            if oid in cache:
               result = (oid, cache[oid])
            else:
                fields = "ObjectID,Name"
                response = self.get(entity, fetch=fields, pagesize=200) # query for all items in entity
                for item in response:
                    cache[item.oid] = item.Name
                if oid in cache:
                    result = (oid, cache[oid])

            self.hydration = hydrationSetting

        return result


    def getAllowedValues(self, entityName, attributeName, **kwargs):
        """
            Given an entityName and and attributeName (assumed to be valid for the entityName)
            issue a request to obtain a list of allowed values for the attribute.
        """
        # get rid of any pesky spaces in the attributeName
        attrName = attributeName.replace(' ', '')
        resource = '%s/%s/allowedValues.js' % (entityName, attrName)
        context, augments = self.contextHelper.identifyContext(**kwargs)
        if augments:
            resource += ("?" + "&".join(augments))
        full_resource_url = "%s/%s" % (self.service_url, resource)
        self._log.debug("GET %s",resource)
        try:
            response = self.session.get(full_resource_url, headers=RALLY_REST_HEADERS)
        except Exception as ex:
            exception_type, value, traceback = sys.exc_info()
            warning('%s: %s\n' % (exception_type, value)) 
            sys.exit(9)

        self._log.debug("%s %s", response.status_code, resource)
        if not response or response.status_code != 200:
            problem = "AllowedValues unobtainable for %s.%s" % (entityName, attrName)
            raise RallyRESTAPIError('%s %s' % (response.status_code, problem))

        try:
            allowed_values_dict = json.loads(response.content)
            return allowed_values_dict
        except Exception as ex:
            print "Unable to decode the json.loads target"
            print ex.args[0]
            return None


    def addAttachment(self, artifact, filename, mime_type='text/plain'):
        """
            Given an artifact (actual or FormattedID for an artifact), validate
            that it exists and then attempt to add an Attachment with the name and
            contents of filename into Rally and associate that Attachment 
            with the Artifact.
            Upon the successful creation of the Attachment and linkage to the artifact,
            return an instance of the succesfully added Attachment.
            Exceptions are raised for other error conditions, such as the filename
            identified by the filename parm not existing, or not being a file, or the 
            attachment file exceeding the maximum allowed size, or failure
            to create the AttachmentContent or Attachment.
           
        """
        # determine if artifact exists, if not short-circuit False
        # determine if attachment already exists for filename (with same size and content)
        #   if so, and already attached to artifact, short-circuit True
        #   if so, but not attached to artifact, save attachment
        #   if not, create the AttachmentContent with filename content, 
        #           create the Attachment with basename for filename and ref the AttachmentContent 
        #              and supply the ref for the artifact in the Artifact field for Attachment
        #
        if not os.path.exists(filename):
            raise Exception('Named attachment filename: %s not found' % filename)
        if not os.path.isfile(filename):
            raise Exception('Named attachment filename: %s is not a regular file' % filename)

        attachment_file_name = os.path.basename(filename)
        attachment_file_size = os.path.getsize(filename)
        if attachment_file_size > self.MAX_ATTACHMENT_SIZE:
            raise Exception('Attachment file size too large, unable to attach to Rally Artifact')

        art_type, artifact = self._realizeArtifact(artifact)
        if not art_type:
            return False

        current_attachments = [att for att in artifact.Attachments]

        response = self.get('Attachment', fetch=True, query='Name = "%s"' % attachment_file_name)
        if response.resultCount:
            attachment = response.next()
            already_attached = [att for att in current_attachments if att.oid == attachment.oid]
            if already_attached:
                return already_attached[0]

        contents = ''
        with open(filename, 'r') as af:
            contents = base64.encodestring(af.read())

        # create an AttachmentContent item
        ac = self.create('AttachmentContent', {"Content" : contents}, project=None)
        if not ac:
            raise RallyRESTAPIError('Unable to create AttachmentContent for %s' % attachment_file_name)
          
        attachment_info = { "Name"        :  attachment_file_name,
                            "Content"     :  ac.ref,       # ref to AttachmentContent
                            "ContentType" :  mime_type,    
                            "Size"        :  attachment_file_size, # must be size before encoding!!
                            "User"        :  'user/%s' % self.contextHelper.user_oid,
                           #"Artifact"    :  artifact.ref  # (Artifact is an 'optional' field)
                          }
        # While it's actually possible to have an Attachment not linked to an Artifact,
        # in most cases, it'll be far more useful to have the linkage to an Artifact than not.
        if artifact:  
            attachment_info["Artifact"] = artifact.ref

        # and finally, create the Attachment
        attachment = self.create('Attachment', attachment_info, project=None)
        if not attachment:
            raise RallyRESTAPIError('Unable to create Attachment for %s' % attachment_file_name)

        return attachment


    def addAttachments(self, artifact, attachments):
        """
            Attachments must be a list of dicts, with each dict having key-value
            pairs for Name, MimeType (or mime_type or content_type or ContentType), Content
        """
        candidates = []
        attached   = []
        for attachment in attachments:
            att_name = attachment.get('Name', None)
            if not att_name:
                continue
            ct_item =     attachment.get('mime_type',    None) or attachment.get('MimeType',    None) \
                      or  attachment.get('content_type', None) or attachment.get('ContentType', None)
            if not ct_item:
                print "Bypassing attachment for %s, no mime_type/ContentType setting..." % att_name
                continue
            candidates.append(att_name)
            upd_artifact = self.addAttachment(artifact, att_name, mime_type=ct_item)
            if upd_artifact:
                attached.append(att_name)
        return len(attached) == len(candidates)


    def getAttachment(self, artifact, filename):
        """
            Given a real artifact instance or the FormattedID of an existing artifact,
            obtain the attachment named by filename.  If there is such an attachment,
            return an Attachment instance with hydration for  Name, Size, ContentType, Content, 
            CreationDate and the User that supplied the attachment.
            If no such attachment is present, return None
        """
        art_type, artifact = self._realizeArtifact(artifact)
        if not art_type:
            return False

        current_attachments = [att for att in artifact.Attachments]
        hits = [att for att in current_attachments if att.Name == filename]
        if not hits:
            return None
        att = hits.pop(0)
        if not att._hydrated:
            getattr(att, 'Description')  # forces the hydration to occur

        # For reasons that are unclear, a "normal" pyral GET on 'AttachmentContent' comes 
        # back as empty even if the specific OID for an AttachmentContent item exists.
        # The target URL of the GET has to be constructed in a particular manner.
        # Fortunately, our _getResourceByOID method fills this need.  
        # But, we have to turn the raw response into a RallyRESTResponse ourselves here.

        context, augments = self.contextHelper.identifyContext()
        resp = self._getResourceByOID(context, 'AttachmentContent', att.Content.oid, project=None)
        if resp.status_code not in [200, 201, 202]:
            return None

        response = RallyRESTResponse(self.session, context, "AttachmentContent.x", resp, "full", 1)
        if response.errors or response.resultCount != 1:
            return None
        att_content = response.next()
        att.Content = base64.decodestring(att_content.Content)  # maybe further txfm to Unicode ?
        return att


    def getAttachmentNames(self, artifact):
        """
            For the given Artifact, return the names (filenames) of the Attachments
        """
        names = []
        if artifact.Attachments:
            names = [att.Name for att in artifact.Attachments]
        return names
        

    def getAttachments(self, artifact):
        """
            For the given Artifact, return a list of Attachment records.
            Each Attachment record will look like a Rally WSAPI Attachment with
            the additional Content attribute that will contain the decoded AttachmentContent.
        """
        attachment_names = self.getAttachmentNames(artifact)
        attachments = [self.getAttachment(artifact, attachment_name) for attachment_name in attachment_names]
        attachments = [att for att in attachments if att is not None]
        return attachments


    def __disabled__deleteAttachment(self, artifact, filename):
        """
            Unfortunately, at this time (WSAPI 1.34+) while AttachmentContent items can be deleted,
            Attachment items cannot.  So, exposing this method would offer very limited utility.
        """
        return False

        art_type, artifact = self._realizeArtifact(artifact)
        if not art_type:
            return False

        current_attachments = [att for att in artifact.Attachments]
        hits = [att for att in current_attachments if att.Name == filename]
        if not hits:
            return False

        # get the target Attachment and the associated AttachmentContent item
        attachment = hits.pop(0)
        print attachment.details()
        if attachment.Content and attachment.Content.oid:
            success = self.delete('AttachmentContent', attachment.Content.oid, project=None)
##
##            print "deletion attempt on AttachmentContent %s succeeded? %s" % (attachment.Content.oid, success)
##
            if not success:
                print "Panic!  unable to delete AttachmentContent item for %s" % attachment.Name
                return False

#        # Squeamishness about the drawbacks of deleting certain entities in Rally has
#        # sloshed into the Attachment realm, so can't actually do a delete of an Attachment.
#### 2012-09-24  re-attempt to delete an Attachment with Rally WSAPI 1.37
####             attempt failed, no Exception raised, but Attachment not deleted...
####
#        #deleted = self.delete('Attachment', attachment.oid, project=None)
#
#        # But, we can still just not include the targeted Attachment here from 
#### 2012-09-20  in fact, this is now dysfunctional also as of WSAPI 1.37 backward incompatible changes
#        # being included in the list of Attachments for our target artifact
#        remaining_attachments = [att for att in current_attachments if att.ref != attachment.ref]
#        att_refs = [dict(_ref=str(att.ref)) for att in remaining_attachments]
#        artifact_info = { 'ObjectID'    : artifact.ObjectID,
#                          'Attachments' : att_refs,
#                        }
#        updated = self.update(art_type, artifact_info, project=None)
#        if updated:
#            return updated
#        else: 
#            return False


    def _realizeArtifact(self, artifact):
        """
            Helper method to identify the artifact type and to retrieve it if the 
            artifact value is a FormattedID. If the artifact is already an instance
            of a Rally entity, then all that needs to be done is deduce the art_type
            from the class name.  If the artifact argument given is neither of those 
            two conditions, return back a 2 tuple of (False, None).
            Once you have an Rally instance of the artifact, return back a 
            2 tuple of (art_type, artifact)
        """
        art_type = False
        if 'pyral.entity.' in str(type(artifact)):
            # we've got the artifact already...
            art_type = artifact.__class__.__name__
        elif self.FORMATTED_ID_PATTERN.match(artifact): 
            # artifact is a potential FormattedID value
            prefix = artifact[:2]
            if prefix[1] in string.digits:
                prefix = prefix[0]
            art_type = self.ARTIFACT_TYPE[prefix]
            response = self.get(art_type, fetch=True, query='FormattedID = %s' % artifact)
            if response.resultCount == 1:
                artifact = response.next()
            else:
                art_type = False
        else: # artifact isn't anything we can deal with here...
            pass

        return art_type, artifact

##################################################################################################
