#!/usr/local/bin/python3.5

###################################################################################################
#
#  pyral.restapi - Python Rally REST API module
#          round 14 support for multi-element-path Project names, couple of minor defect fixes
#          notable dependencies:
#               requests v2.8.1 or better
#
###################################################################################################

__version__ = (1, 2, 4)

import sys, os
import re
import types
import time
import six
from   six.moves.urllib.parse import quote, unquote
import json
import string
import base64
from operator import itemgetter
from pprint   import pprint

import requests   

# intra-package imports
from .config  import PROTOCOL, SERVER, WS_API_VERSION, WEB_SERVICE, SCHEMA_SERVICE, AUTH_ENDPOINT
from .config  import RALLY_REST_HEADERS
from .config  import USER_NAME, PASSWORD 
from .config  import START_INDEX, MAX_PAGESIZE, MAX_ITEMS
from .config  import timestamp
from .search_utils  import projectAncestors, projectDescendants, projeny, flatten, MockRallyRESTResponse

###################################################################################################

# 
# define a module global that should be set up/known before a few more module imports
#
_rallyCache = {}  # keyed by a context tuple (server, user, password, workspace, project)
                  # value is a dict with at least:
                  # a key of 'rally'    whose value there is a Rally instance  and
                  # a key of 'hydrator' whose value there is an EntityHydrator instance

def warning(message):
    sys.stderr.write("WARNING: %s\n" % message)

SERVICE_REQUEST_TIMEOUT   = 120
HTTP_REQUEST_SUCCESS_CODE = 200
PAGE_NOT_FOUND_CODE       = 404

PROJECT_PATH_ELEMENT_SEPARATOR = ' // '

###################################################################################################

class RallyRESTAPIError(Exception): pass
class RallyAttributeNameError(Exception): pass

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
##    print("getResourceByOID called:")
##    print("   context: %s" % context)
##    print("    entity: %s" % entity)
##    print("       oid: %s" % oid)
##    print("    kwargs: %s" % kwargs)
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
##
##        print("_rallyCache.keys:")
##        for key in _rallyCache.keys():
##            print("    -->%s<--" % key)
##        print("")
##        print(" apparently no key to match: -->%s<--" % context)
##        print(" context is a %s" % type(context))
##
    rally = rallyContext.get('rally')
    resp = rally._getResourceByOID(context, entity, oid, **kwargs)
    if 'unwrap' not in kwargs or not kwargs.get('unwrap', False):
        return resp
    response = RallyRESTResponse(rally.session, context, "%s.x" % entity, resp, "full", 1)
    return response

def getCollection(context, collection_url, **kwargs):
    """
        Retrieves a reference in _rallyCache to a Rally instance and uses that to 
        call its getCollection method.
        Returns a RallyRESTResponse instance that has status_code, headers and content attributes.
    """
    global _rallyCache
    rallyContext = _rallyCache.get(context, None)
    if not rallyContext:
        ck_matches = [rck for rck in list(_rallyCache.keys()) if rck.identity() == context.identity()]
        if ck_matches:
            rck = ck_matches.pop()
            rallyContext = _rallyCache[rck]
        else:
            # raising an Exception is the only thing we can do, don't see any prospect of recovery...
            raise RallyRESTAPIError('Unable to find Rally instance for context: %s' % context)
    rally = rallyContext.get('rally')
    response = rally.getCollection(collection_url, **kwargs)
    return response


#  these imports have to take place after the prior class and function defs 
from .rallyresp import RallyRESTResponse, ErrorResponse
from .hydrate   import EntityHydrator
from .context   import RallyContext, RallyContextHelper
from .entity    import validRallyType, DomainObject
from .query_builder import RallyUrlBuilder

__all__ = ["Rally", "getResourceByOID", "getCollection", "hydrateAnInstance", "RallyUrlBuilder"]


def _createShellInstance(context, entity_name, item_name, item_ref):
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
    FORMATTED_ID_PATTERN = re.compile(r'^[A-Z]{1,2}\d+$') #S|US|DE|DS|TA|TC|TS|PI
    MAX_ATTACHMENT_SIZE = 50000000  # approx 50 MB 

    def __init__(self, server=SERVER, user=None, password=None, apikey=None,
                       version=WS_API_VERSION, warn=True, server_ping=None, 
                       isolated_workspace=False, **kwargs):
        self.server       = server 
        self.user         = user     or USER_NAME
        self.password     = password or PASSWORD
        self.apikey       = apikey
        self.version      = WS_API_VERSION  # we only support v2.0 now
        self._inflated    = False
        self.service_url  = "%s://%s/%s" % (PROTOCOL, self.server, WEB_SERVICE    % self.version)
        self.schema_url   = "%s://%s/%s" % (PROTOCOL, self.server, SCHEMA_SERVICE % self.version)
        self.hydration    = "full"
        self._sec_token   = None
        self._log         = False
        self._logDest     = None
        self._logAttrGet  = False
        self._warn        = warn
        self._server_ping = True   # this is the default for 1.2.0
        if 'RALLY_PING' in os.environ:
            if os.environ['RALLY_PING'].lower() in ['f', 'false', 'n', 'no', '0']:
                self._server_ping = False
        if server_ping == False:
            self._server_ping = False
        self.isolated_workspace = isolated_workspace
        config = {}
        if kwargs and 'debug' in kwargs and kwargs.get('debug', False):
            config['verbose'] = sys.stdout

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
##
##        print("\n requests lib in %s" % requests.__file__)
##
        self.session = requests.Session()
        self.session.headers = RALLY_REST_HEADERS
        if self.apikey:
            self.session.headers['ZSESSIONID'] = self.apikey
            self.user     = None
            self.password = None
        else:
            self.session.auth = requests.auth.HTTPBasicAuth(self.user, self.password)
        self.session.timeout = 10.0
        self.session.proxies = proxy_dict
        self.session.verify  = verify_ssl_cert
        self.session.config  = config
        
        global _rallyCache

        self.contextHelper = RallyContextHelper(self, self.server, self.user, self.password or self.apikey, 
                                                      self._server_ping)
        _rallyCache[self.contextHelper.context] = {'rally' : self }
        wksp = None
        proj = None
        if 'workspace' in kwargs and kwargs['workspace'] and kwargs['workspace']!= 'default':
            wksp = kwargs['workspace']
        if 'project' in kwargs and kwargs['project'] and kwargs['project']!= 'default':
            proj = kwargs['project']
        self.contextHelper.check(self.server, wksp, proj, self.isolated_workspace)

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
                 warning("Unable to use your workspace specification, that value is not listed in your subscription")
                  
        if 'project' in kwargs and kwargs['project'] != self.contextHelper.currentContext().project \
                               and kwargs['project'] != 'default':

            mep_proj = None
            accessibleProjects = [name for name, ref in self.contextHelper.getAccessibleProjects(workspace='current')]
            if PROJECT_PATH_ELEMENT_SEPARATOR in kwargs['project']:  # is ' // ' in kwargs['project']?
                mep_proj = self.contextHelper._findMultiElementPathToProject(kwargs['project'])
                if mep_proj:
                    accessibleProjects.append(kwargs['project'])

            if kwargs['project'] in accessibleProjects:
                if not mep_proj:
                    self.contextHelper.setProject(kwargs['project'])
                else:
                    self.contextHelper.setProject(mep_proj.ref, name=kwargs['project'])
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
                    prob = "Default project changed to '%s' (%s).\n" + \
                           "         Your normal default project: '%s' is not valid for\n" +\
                           "         the current workspace setting of: '%s'"
                    short_proj_ref = "/".join(ndp_ref.split('/')[-2:])
                    wksp_name, wksp_ref = self.contextHelper.getWorkspace()
                    warning(prob % (ndp_name, short_proj_ref, cdp_name, wksp_name))

        if __adjust_cache:
            _rallyCache[self.contextHelper.currentContext()] = {'rally' : self}


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


    def obtainSecurityToken(self):
        if self.apikey:
            return None

        if not self._sec_token:
            security_service_url = "%s/%s" % (self.service_url, AUTH_ENDPOINT)
            response = self.session.get(security_service_url)
            doc = response.json()
            self._sec_token = str(doc['OperationResult']['SecurityToken'])

        return self._sec_token


    def enableLogging(self, dest=sys.stdout, attrget=False, append=False):
        """
            Use this to enable logging. dest can set to the name of a file or an open file/stream (writable). 
            If attrget is set to true, all Rally REST requests that are executed to obtain attribute information
            will also be logged. Be careful with that as the volume can get quite large.
            The append parm controls whether any existing file will be appended to or overwritten.
        """
        self._log = True
        if hasattr(dest, 'write'):
            self._logDest = dest
        elif type(dest) == bytes:
            try:
                mode = 'w'
                if append:
                    mode = 'a'
                self._logDest = open(dest, mode)
            except IOError as ex:
                self._log = False
                self._logDest = None
        else:
            self._log = False
            # emit a warning that logging is disabled due to a faulty dest arg
            warning('Logging dest arg cannot be written to, proceeding with logging disabled.')
        if self._log:     
            scopeNote = '%s Following entries record Rally REST API interaction via %s for user: %s' % \
                        (timestamp(), self.service_url, self.user)
            self._logDest.write('%s\n' % scopeNote)
            self._logDest.flush()
            if attrget:
                self._logAttrGet = True


    def disableLogging(self):
        """
            Disable logging. 
        """
        if self._log:
            self._log = False
            self._logAttrGet = False
            if self._logDest and self._logDest not in (sys.stdout, sys.stderr):
                try:
                    self._logDest.flush()
                    self._logDest.close()
                except IOError as ex:
                    # emit a warning that the logging destination was unable to be closed
                    pass
                self._logDest = None

    def enableWarnings(self):
        self._warn = True

    def disableWarnings(self):
        self._warn = False

    def warningsEnabled(self):
        return self._warn == True


    def subscriptionName(self):
        """
            Returns the name of the subscription in the currently active context.
        """
        return self.contextHelper.currentContext().subscription()


    def setWorkspace(self, workspaceName):
        """
            Given a workspaceName, set that as the currentWorkspace and use the ref for 
            that workspace in subsequent interactions with Rally.
            However, if the instance was realized using the keyword arg isolated_workspace = True
            then do not permit the workspace switch to take place, raise an Exception.
        """
        if self.isolated_workspace and workspaceName != self.getWorkspace().Name:
            problem = "No reset of of the Workspace is permitted when the isolated_workspace option is specified"
            raise RallyRESTAPIError(problem)
        if not self.contextHelper.isAccessibleWorkspaceName(workspaceName):
            raise Exception('Specified workspace not valid for your credentials or is in a Closed state')
        self.contextHelper.setWorkspace(workspaceName)


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
            that project in subsequent interractions with Rally unless overridden.
            If the projectName contains the ' // ' path element separator token string and there are
            two or more path elements in the deconstructed string, the verify that the project path
            given is valid and use that project and ref are used in subsequent interactions with Rally
            unless overridden.
        """
        context = self.contextHelper.currentContext()
        if PROJECT_PATH_ELEMENT_SEPARATOR not in projectName:  # is ' // ' in projectName?
            eligible_projects = [proj for proj,ref in self.contextHelper.getAccessibleProjects(workspace='current')]
            if projectName not in eligible_projects:
                raise Exception('Specified project not valid for your current workspace or credentials')
            self.contextHelper.setProject(projectName)
        else:  # projectName name like baseProject // nextLevelProject // targetProject
            proj = self.contextHelper._findMultiElementPathToProject(projectName)
            if not proj:
                raise Exception('Specified projectName not found or not valid for your current workspace or credentials')
            #proj = _createShellInstance(context, 'Project', projectName, proj._ref)
            self.contextHelper.setProject(proj.ref, name=projectName)


    def getProject(self, name=None):
        """
            Returns a minimally hydrated Project instance with the Name and ref
            of the project in the currently active context if the name keyword arg
            is not supplied or the Name and ref of the project identified by the name
            as long as the name identifies a valid project in the currently selected workspace.
            If the name keyword arg has the form of fully qualified path using the ' // ' path
            element separator token, then specialized pyral machinery will attempt to "chase"
            the elements until either an invalid path element is detected or all path elements
            are valid and the name and ref of the ending Project path element is returned.
            Returns None if a name parameter is supplied that does not identify a valid project
            in the currently selected workspace.
        """
        context = self.contextHelper.currentContext()
        if not name:
            proj_name, proj_ref = self.contextHelper.getProject()
##
##            print("Rally.getProject called contextHelper.getProject, it returned %s and %s" % (proj_name, proj_ref))
##
            return _createShellInstance(context, 'Project', proj_name, proj_ref)

        if name and PROJECT_PATH_ELEMENT_SEPARATOR in name:
            proj = self.contextHelper._findMultiElementPathToProject(name)
            if proj:
                return _createShellInstance(context, 'Project', name, proj._ref)

        projs = self.contextHelper.getAccessibleProjects(workspace='current')
        hits = [(proj,ref) for proj,ref in projs if str(proj) == str(name)]
        if not hits:
            return None
        tp = hits[0]
        tp_ref = tp[1]
        return _createShellInstance(context, 'Project', name, tp_ref)
        

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
        #context  = self.contextHelper.currentContext()
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
            whose ref and collection attributes will be resolved upon initial access.
        """
        saved_workspace_name, saved_workspace_ref = self.contextHelper.getWorkspace()
        if not workspace:
            workspace = saved_workspace_name
        self.setWorkspace(workspace)

        context, augments = self.contextHelper.identifyContext(workspace=workspace)
        workspace_ref = self.contextHelper.currentWorkspaceRef()

        # Somewhere post 1.3x in Rally WSAPI, the ability to list the User attrs along with the TimeZone
        # attr of UserProfile and have that all returned in 1 query was no longer supported.
        # And somewhere north of v 1.42 and into v2, only a user who is a SubscriptionAdmin
        # can actually get information about another user's UserProfile so the next statement
        # is limited to a Rally instance whose credentials represent a SubscriptionAdmin capable user.
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

        users_resource = 'users?fetch=%s&query=&pagesize=%s&start=1&workspace=%s' % \
                         (",".join(user_attrs), MAX_PAGESIZE, workspace_ref)
        full_resource_url = '%s/%s' % (self.service_url, users_resource)
        response = self.session.get(full_resource_url, timeout=SERVICE_REQUEST_TIMEOUT)
        if response.status_code != HTTP_REQUEST_SUCCESS_CODE:
            return []
        response = RallyRESTResponse(self.session, context, users_resource, response, "full", 0)
        users = [user for user in response]

        # find the operator of this instance of Rally and short-circuit now if they *aren't* a SubscriptionAdmin
        operator = [user for user in users if user.UserName == self.user]
        if not operator or len(operator) == 0 or not operator[0].SubscriptionAdmin:
            self.setWorkspace(saved_workspace_name)
            return users

        user_profile_resource = 'userprofile?fetch=true&query=&pagesize=%s&start=1&workspace=%s' % (MAX_PAGESIZE, workspace_ref)
        response = self.session.get('%s/%s' % (self.service_url, user_profile_resource), 
                                    timeout=SERVICE_REQUEST_TIMEOUT)
        if response.status_code != HTTP_REQUEST_SUCCESS_CODE:
            warning("Unable to retrieve UserProfile information for users")
            profiles = []
        else:
            response = RallyRESTResponse(self.session, context, user_profile_resource, response, "full", 0)
            profiles = [profile for profile in response]

        # do our own brute force "join" operation on User to UserProfile info 
        for user in users:
            # get any matching user profiles (aka mups), there really should only be 1 matching...
            mups = [prof for prof in profiles 
                          if hasattr(user, 'UserProfile') and prof._ref == user.UserProfile._ref] 
            if not mups:
                up = user.UserProfile if hasattr(user, 'UserProfile') else "Unknown"
                problem = "unable to find a matching UserProfile record for User: %s  UserProfile: %s"
               #warning("%s" % (problem % (user.UserName, up)))
                continue
            else:
                if len(mups) > 1:
                    anomaly = "Found %d UserProfile items associated with username: %s"
                    warning("%s" % (anomaly % (len(mups), user.UserName)))
                # now attach the first matching UserProfile to the User
                user.UserProfile = mups[0]

        self.setWorkspace(saved_workspace_name)
        return users


    def _officialRallyEntityName(self, supplied_name):
        if supplied_name in ['Story', 'UserStory', 'User Story']:
            supplied_name = 'HierarchicalRequirement'
        if supplied_name == 'search':
            return supplied_name

        # here's where we'd make an inquiry into entity to see if the supplied_name
        # is a Rally entity on which CRUD ops are permissible.
        # An Exception is raised if not.
        # If supplied_name resolves in some way to a valid Rally entity,
        # this returns either a simple name or a TypePath string (like PortfolioItem/Feature)
        official_name = validRallyType(supplied_name)
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
##        print("in _getResourceByOID, OID specific resource ...", entity, oid)
##        sys.stdout.flush()
##
        resource = '%s/%s' % (entity, oid)
        if '_disableAugments' not in kwargs:
            contextDict = context.asDict()
##
##            print("_getResourceByOID, current contextDict: %s" % repr(contextDict))
##            sys.stdout.flush()
##
            context, augments = self.contextHelper.identifyContext(**contextDict)
            if augments:
                resource += ("?" + "&".join(augments))
##
##            print("_getResourceByOID, modified contextDict: %s" % repr(context.asDict()))
##            sys.stdout.flush()
##
        full_resource_url = "%s/%s" % (self.service_url, resource)
        if self._logAttrGet:
            self._logDest.write('%s GET %s\n' % (timestamp(), resource))
            self._logDest.flush()
##
##        print("issuing GET for resource: %s" % full_resource_url)
##        sys.stdout.flush()
##
        try:
            raw_response = self.session.get(full_resource_url)
        except Exception as ex:
            exctype, value, tb = sys.exc_info()
            warning("%s: %s" % (exctype, value)) 
            return None
##
##        print("_getResourceByOID(%s, %s) raw_response: %s" % (entity, oid, raw_response))
##        sys.stdout.flush()
##
        return raw_response


    def _itemQuery(self, entityName, oid, workspace=None, project=None):
        """
            Internal method to retrieve a specific instance of an entity identified by the OID.
        """
##
##        print("Rally._itemQuery('%s', %s, workspace=%s, project=%s)" % (entityName, oid, workspace, project))
##
        resource = '%s/%s' % (entityName, oid)
        context, augments = self.contextHelper.identifyContext(workspace=workspace, project=project)
        if augments:
            resource += ("?" + "&".join(augments))
        if self._log:
            self._logDest.write('%s GET %s\n' % (timestamp(), resource))
            self._logDest.flush()
        response = self._getResourceByOID(context, entityName, oid)
        if self._log:
            self._logDest.write('%s %s %s\n' % (timestamp(), response.status_code, resource))
            self._logDest.flush()
        if not response or response.status_code != HTTP_REQUEST_SUCCESS_CODE:
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
        collection_attributes = [attr_name for attr_name in list(item_data.keys())
                                            if attr_name.lower == 'children'
                                            or attr_name[-1] == 's'
                                ]
        if not collection_attributes:
            return item_data
        for attr_name in collection_attributes:
            if type(item_data[attr_name]) != list:
                continue
            obj_list = []
            for value in item_data[attr_name]:
                # is value like "someentityname/34223214" ?
                if (type(value) == str or type(value) == bytes) and '/' in value \
                and re.match('^\d+$', value.split('/')[-1]):
                    obj_list.append({"_ref" : value})  # transform to a dict instance
                elif issubclass(value.__class__, DomainObject):
                    obj_list.append({"_ref" : value.ref})  # put the ref in a dict instance
                else:
                    obj_list.append(value)   # value is untouched
            item_data[attr_name] = obj_list
        return item_data


    def _buildRequest(self, entity, fetch, query, order, kwargs):
        pagesize   = MAX_PAGESIZE
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
        if fetch in ['true', 'True', True]:
            fetch = 'true'
            self.hydration = "full"
        elif fetch in ['false', 'False', False]:
            fetch = 'false'
            self.hydration = "shell"
        elif (type(fetch) == bytes or type(fetch) == str) and fetch.lower() != 'false':
            self.hydration = "full"
        elif type(fetch) == tuple and len(fetch) == 1 and fetch[0].count(',') > 0:
            fetch = fetch[0]
        elif type(fetch) in [list, tuple]:
            field_dict = dict([(attr_name, True) for attr_name in fetch]) 
            attr_info = self.validateAttributeNames(entity, field_dict) 
            fetch = ",".join(k for k in list(attr_info.keys()))
            self.hydration = "full"

        entity = self._officialRallyEntityName(entity)
        resource = RallyUrlBuilder(entity)
        resource.qualify(fetch, query, order, pagesize, startIndex)

        if '_disableAugments' in kwargs:
            context = RallyContext(self.server, self.user, self.password or self.apikey, self.service_url)
        else:
            context, augments = self.contextHelper.identifyContext(**kwargs)
            workspace_ref = self.contextHelper.currentWorkspaceRef()
            project_ref   = self.contextHelper.currentProjectRef()
            if workspace_ref:   # TODO: would we ever _not_ have a workspace_ref?
                if 'workspace' not in kwargs or ('workspace' in kwargs and kwargs['workspace'] is not None):
                    resource.augmentWorkspace(augments, workspace_ref)
                    if project_ref:
                        if 'project' not in kwargs or ('project' in kwargs and kwargs['project'] is not None):
                            resource.augmentProject(augments, project_ref)
                            resource.augmentScoping(augments)
        resource = resource.build()  # can also use resource = resource.build(pretty=True)
        full_resource_url = "%s/%s" % (self.service_url, resource)

        return context, resource, full_resource_url, limit


    def _getRequestResponse(self, context, request_url, limit):
        response = None  # in case an exception gets raised in the session.get call ...
        try:
            # a response has status_code, content and data attributes
            # the data attribute is a dict that has a single entry for the key 'QueryResult' 
            # or 'OperationResult' whose value is in turn a dict with values of 
            # 'Errors', 'Warnings', 'Results'
            response = self.session.get(request_url, timeout=SERVICE_REQUEST_TIMEOUT)
        except Exception as ex:
            if response:
##
##                print("Exception detected for session.get requests, response status code: %s" % response.status_code)
##
                ret_code, content = response.status_code, response.content
            else:
                ret_code, content = PAGE_NOT_FOUND_CODE, str(ex.args[0])
            if self._log:
                self._logDest.write('%s %s\n' % (timestamp(), ret_code))
                self._logDest.flush()

            errorResponse = ErrorResponse(ret_code, content)
            response = RallyRESTResponse(self.session, context, request_url, errorResponse, self.hydration, 0)
            return response

##
##        print("response.status_code is %s" % response.status_code)
##
        if response.status_code != HTTP_REQUEST_SUCCESS_CODE:
            if self._log:
                code, verbiage = response.status_code, response.content[:56]
                self._logDest.write('%s %s %s ...\n' % (timestamp(), code, verbiage))
                self._logDest.flush()
##
##            print(response)
##
            #if response.status_code == PAGE_NOT_FOUND_CODE:
            #    problem = "%s Service unavailable from %s, check for proper hostname" % \
            #             (response.status_code, self.service_url)
            #    raise Exception(problem)
            errorResponse = ErrorResponse(response.status_code, response.content)
            response = RallyRESTResponse(self.session, context, request_url, errorResponse, self.hydration, 0)
            return response 

        response = RallyRESTResponse(self.session, context, request_url, response, self.hydration, limit)

        if self._log:
            if response.status_code == HTTP_REQUEST_SUCCESS_CODE:
                #req_target = "/".join(request_url.split('/'))
                slm_ws_ver = '/%s/' % (WEB_SERVICE % WS_API_VERSION)
                req_target, oid = request_url.split(slm_ws_ver)[-1].rsplit('/', 1)
                desc = '%s TotalResultCount %s' % (req_target, response.resultCount)
            else:
                desc = response.errors[0]
            self._logDest.write('%s %s %s\n' % (timestamp(), response.status_code, desc))
            self._logDest.flush()

        return response


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
        context, resource, full_resource_url, limit = self._buildRequest(entity, fetch, query, order, kwargs)
##
##        print("full_resource_url: %s" % full_resource_url)
##
        if self._log: 
            # unquote the resource for enhanced readability
            self._logDest.write('%s GET %s\n' % (timestamp(), unquote(resource)))
            self._logDest.flush()

        response = self._getRequestResponse(context, full_resource_url, limit)
            
        if kwargs and 'instance' in kwargs and kwargs['instance'] == True and response.resultCount == 1:
            return response.next()
        return response

    find = get # offer interface approximately matching Ruby Rally REST API, App SDK Javascript RallyDataSource


    def put(self, entityName, itemData, workspace='current', project='current', **kwargs):
        """
            Given a Rally entityName, a dict with data that the newly created entity should contain,
            issue the REST call and return the newly created target entity item.
        """
        auth_token = self.obtainSecurityToken()
        # raises a RallyAttributeNameError if any attribute names in itemData are invalid
        # see if we need to transform workspace / project values of 'current' to actual
        if workspace == 'current':
            workspace = self.getWorkspace().Name  # just need the Name here
        if project == 'current':
            project = self.getProject().Name  # just need the Name here

        entityName = self._officialRallyEntityName(entityName)
        if entityName.lower() == 'recyclebinentry':
            raise RallyRESTAPIError("create operation unsupported for RecycleBinEntry")

        resource = "%s/create?key=%s" % (entityName.lower(), auth_token)
        context, augments = self.contextHelper.identifyContext(workspace=workspace, project=project)
        if augments:
            resource += ("&" + "&".join(augments))
        full_resource_url = "%s/%s" % (self.service_url, resource)

        itemData = self.validateAttributeNames(entityName, itemData) 
        item = {entityName: self._greased(itemData)} # where _greased is a convenience
                                                     # method that will transform
                                                     # any ref lists for COLLECTION attributes
                                                     # into a list of one-key dicts {'_ref' : ref}
        payload = json.dumps(item)
        if self._log:
            self._logDest.write('%s PUT %s\n%27.27s %s\n' % (timestamp(), resource, " ", payload))
            self._logDest.flush()
        response = self.session.put(full_resource_url, data=payload, headers=RALLY_REST_HEADERS)
        response = RallyRESTResponse(self.session, context, resource, response, "shell", 0)
        if response.status_code != HTTP_REQUEST_SUCCESS_CODE:
            desc = str(response.errors[0])
            problem = "%s %s" % (response.status_code, desc)
            #print(problem)
            if self._log:
                self._logDest.write('%s %s\n' % (timestamp(), problem))
                self._logDest.flush()
            raise RallyRESTAPIError(problem)

        item = response.content['CreateResult']['Object']
        ref  = str(item['_ref'])
        item_oid = int(ref.split('/')[-1])
        desc = "created %s OID: %s" % (entityName, item_oid)
        if self._log:
            self._logDest.write('%s %s %s\n' % (timestamp(), response.status_code, desc))
            self._logDest.flush()

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
        auth_token = self.obtainSecurityToken()
        # see if we need to transform workspace / project values of 'current' to actual
        if workspace == 'current':
            workspace = self.getWorkspace().Name  # just need the Name here
        if project == 'current':
            project = self.getProject().Name  # just need the Name here

        entityName = self._officialRallyEntityName(entityName)
        if entityName.lower() == 'recyclebinentry':
            raise RallyRESTAPIError("update operation unsupported for RecycleBinEntry")

        oid = itemData.get('ObjectID', None)
        if not oid:
            formattedID = itemData.get('FormattedID', None)
            if not formattedID:
                raise RallyRESTAPIError('An identifying field (ObjectID or FormattedID) must be specified')
            fmtIdQuery = 'FormattedID = "%s"' % formattedID
            response = self.get(entityName, fetch="ObjectID", query=fmtIdQuery, 
                                workspace=workspace, project=project)
            if response.status_code != HTTP_REQUEST_SUCCESS_CODE or response.resultCount == 0:
                raise RallyRESTAPIError('Target %s %s could not be located' % (entityName, formattedID))
                
            target = response.next()
            oid = target.ObjectID
            itemData['ObjectID'] = oid

        resource = '%s/%s?key=%s' % (entityName.lower(), oid, auth_token) 
        context, augments = self.contextHelper.identifyContext(workspace=workspace, project=project)
        if augments:
            resource += ("&" + "&".join(augments))
        full_resource_url = "%s/%s" % (self.service_url, resource)
        itemData = self.validateAttributeNames(entityName, itemData) 
        item = {entityName: self._greased(itemData)}
        payload = json.dumps(item)
        if self._log:
            self._logDest.write('%s POST %s\n%27.27s %s\n' % (timestamp(), resource, " ", item))
            self._logDest.flush()
        response = self.session.post(full_resource_url, data=payload, headers=RALLY_REST_HEADERS)
        response = RallyRESTResponse(self.session, context, resource, response, "shell", 0)
        if response.status_code != HTTP_REQUEST_SUCCESS_CODE:
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
        auth_token = self.obtainSecurityToken()
        # see if we need to transform workspace / project values of 'current' to actual
        if workspace == 'current':
            workspace = self.getWorkspace().Name  # just need the Name here
        if project == 'current':
            project = self.getProject().Name  # just need the Name here

        entityName = self._officialRallyEntityName(entityName)

        # guess at whether itemIdent is an ObjectID or FormattedID via 
        # regex matching (all digits or 1-2 upcase chars + digits)
        objectID = itemIdent  # at first assume itemIdent is the ObjectID
        if re.match('^[A-Z]{1,2}\d+$', str(itemIdent)):
            fmtIdQuery = 'FormattedID = "%s"' % itemIdent
            response = self.get(entityName, fetch="ObjectID", query=fmtIdQuery, 
                                workspace=workspace, project=project)
            if response.status_code != HTTP_REQUEST_SUCCESS_CODE:
                raise RallyRESTAPIError('Target %s %s could not be located' % (entityName, itemIdent))
                
            target = response.next()
            objectID = target.ObjectID
##
##            if kwargs.get('debug', False):
##               print("DEBUG: target OID -> %s" % objectID)
##
        resource = "%s/%s?key=%s" % (entityName.lower(), objectID, auth_token)
        context, augments = self.contextHelper.identifyContext(workspace=workspace, project=project)
        if augments:
            resource += ("&" + "&".join(augments))
        full_resource_url = "%s/%s" % (self.service_url, resource)
        if self._log:
            self._logDest.write('%s DELETE %s\n' % (timestamp(), resource))
        response = self.session.delete(full_resource_url, headers=RALLY_REST_HEADERS)
        if response and response.status_code != HTTP_REQUEST_SUCCESS_CODE:
            if self._log:
                self._logDest.write('%s %s %s ...\n' % \
                       (timestamp(), response.status_code, response.content[:56]))
                self._logDest.flush()
##
##            if kwargs.get('debug', False):
##                print(response.status_code, response.headers, response.content)
##
            errorResponse = ErrorResponse(response.status_code, response.content)
            response = RallyRESTResponse(self.session, context, resource, errorResponse, self.hydration, 0)
            problem = "ERRORS: %s\nWARNINGS: %s\n" % ("\n".join(response.errors), 
                                                      "\n".join(response.warnings))
            raise RallyRESTAPIError(problem)

##
##        print(response.content)
##
        response = RallyRESTResponse(self.session, context, resource, response, "shell", 0)
        if response.errors:
            status = False
            desc = response.errors[0]
        else:
            status = True
            desc = '%s deleted' % entityName
        if self._log:
            self._logDest.write('%s %s %s\n' % (timestamp(), response.status_code, desc))
            self._logDest.flush()

        return status


    def getCollection(self, collection_url, **kwargs):
        """
            Given a collection_url of the form:
                http(s)://<server>(:<port>)/slm/webservice/v2.0/<entity>/OID/<attribute>
            issue a request for the url and return back a list of hydrated instances for each item 
            in the collection.
        """
        context = self.contextHelper.currentContext()
        # craven ugly hackiness to support calls triggered from within ContextHelper.check ...
        if not '?fetch=' in collection_url:
            collection_url = "%s?pagesize=%d&start=1" % (collection_url, MAX_PAGESIZE)
        resource = collection_url

        disabled_augments = kwargs.get('_disableAugments', False)
        if not disabled_augments:
            workspace_ref = self.contextHelper.currentWorkspaceRef()
            project_ref   = self.contextHelper.currentProjectRef()
            resource = "%s&workspace=%s&project=%s" % (resource, workspace_ref, project_ref)
##
##        print("Collection resource URL: %s" % resource)
##
        if self._log: 
            self._logDest.write('%s GET %s\n' % (timestamp(), resource))
            self._logDest.flush()
        rally_rest_response = self._getRequestResponse(context, resource, 0)
        return rally_rest_response


    def addCollectionItems(self, target, items):
        """
            Given a target which is a hydrated RallyEntity instance having a valid _type
            and a a list of hydrated Rally Entity instances (items)
            all of the same _type, construct a valid AC WSAPI collection url and 
            issue a POST request to that URL supplying the item refs in an appropriate
            JSON structure as the payload.
        """
        if not items: return None
        auth_token = self.obtainSecurityToken()
        target_type = target._type
        item_types = [item._type for item in items]
        item_type = item_types[0]
        outliers = [item for item in item_types if item._type != item_type]
        if outliers:
            raise RallyRESTAPIError("addCollectionItems: all items must be of the same type")

        resource = "%s/%s/%ss/add" % (target_type, target.oid, item_type)
        collection_url = '%s/%s?fetch=Name&key=%s' % (self.service_url, resource, auth_token)
        payload = {"CollectionItems":[{'_ref' : "%s/%s" % (str(item._type), str(item.oid))} 
                    for item in items]}
        response = self.session.post(collection_url, data=json.dumps(payload), headers=RALLY_REST_HEADERS)
        context = self.contextHelper.currentContext()
        response = RallyRESTResponse(self.session, context, resource, response, "shell", 0)
        added_items = [str(item[u'Name']) for item in response.data[u'Results']]
        return added_items


    def dropCollectionItems(self, target, items):
        """
            Given a target which is a hydrated RallyEntity instance having a valid _type
            and a items which is a list of hydrated Rally Entity instances
            all of the same _type, construct a valid AC WSAPI collection url and 
            issue a POST request to that URL supplying the item refs in an appropriate
            JSON structure as the payload.
        """
        if not items: return None
        auth_token = self.obtainSecurityToken()
        target_type = target._type
        item_type = items[0]._type
        resource = "%s/%s/%ss/remove" % (target_type, target.oid, item_type)
        collection_url = '%s/%s?key=%s' % (self.service_url, resource, auth_token)
        payload = {"CollectionItems":[{'_ref' : "%s/%s" % (str(item._type), str(item.oid))} 
                    for item in items]}
        response = self.session.post(collection_url, data=json.dumps(payload), headers=RALLY_REST_HEADERS)
        context = self.contextHelper.currentContext()
        response = RallyRESTResponse(self.session, context, resource, response, "shell", 0)
        return response


    def search(self, keywords, **kwargs):
        """
            Given a list of keywords or a string with space separated words, issue
            the relevant Rally WSAPI search request to find artifacts within the search
            scope that have any of the keywords in any of the artifact's text fields.

            https://rally1.rallydev.com/slm/webservice/v2.x/search?
                _slug=%2Fsearch
                &project=%2Fproject%2F3839949386
                &projectScopeUp=false
                &projectScopeDown=true
                &searchScopeOid=3839949386   # in this case it is the Project ObjectID
                &searchScopeUp=false
                &searchScopeDown=true
                &searchScopeType=project
                &keywords=wsapi%20documentation
                &fetch=true
                &recycledItems=true
                &includePermissions=true
                &compact=true
                &start=1
                &pagesize=25

             defaults:
                 projectScopeUp=false
                 projectScopeDown=false
                 includePermissions=true
                 recycledItems=false
                 compact=true

             A successful search returns SearchObject instances, which have the useful attributes of:
                ObjectID
                FormattedID
                Name
                Project
                MatchingText
                LastUpdateDate
        """
        context = self.contextHelper.currentContext()
        kwargs['_slug'] = "/search"
        kwargs['pagesize'] = 200
        kwargs['searchScope'] = 'project'
        if 'projectScopeUp' not in kwargs:
            kwargs['projectScopeUp'] = False
        if 'projectScopeDown' not in kwargs:
            kwargs['projectScopeDown'] = False

        # unfortunately, the WSAPI seems to not recognize/operate on projectScopeX, searchScopeX parameters...
        #kwargs['searchScopeUp'] = 'false'
        #kwargs['searchScopeDown'] = 'false'
        #if getattr(kwargs, 'projectScopeUp', False):
        #    kwargs['searchScopeUp'] = 'true'
        #if getattr(kwargs, 'projectScopeDown', False):
        #    kwargs['searchScopeDown'] = 'true'

        fields = "ObjectID,FormattedID,Name,Project,MatchingText,LastUpdatedDate"
        context, resource, resource_url, limit = self._buildRequest('search', fields, None, None, kwargs)

        # so don't bother with including the searchScopeX in the resource_url query_string
        #left, right = resource_url.split('&pagesize=')
        #left += "&searchScope=project"
        #ssu = 'true' if getattr(kwargs, 'searchScopeUp', False) else 'false'
        #ssd = 'true' if getattr(kwargs, 'searchScopeDown', False) else 'false'
        #left += "&searchScopeUp=%s&searchScopeDown=%s" % (ssu, ssd)
        #resource_url = "%s&pagesize=%s" % (left, right)

        url, query_string = resource_url.split('?', 1)
        resource_url = "%s?keywords=%s&%s" % (url, quote(keywords), query_string)
##
##        print(resource_url)
##
        response = self._getRequestResponse(context, resource_url, limit)
        if response.errors:
            error_text = response.errors[0]
            raise RallyRESTAPIError(error_text)
##
##        print(response.data)
##

        # since the WSAPI apparently doesn't pay attention to scoping (projectScopeUp, projectScopeDown, searchScopeUp, searchScopeDown)
        # let's take care of the intended scoping here and provide back to the caller the
        # resultCount as well as the iterable with the SearchObject instances.

        # if the projectScopeUp and projectScopeDown are False
        #     only capture the SearchObject instances whose Project attribute matches our current context Project Name
        # if the projectScopeUp is True and the projectScopeDown is False
        #    only capture the SearchObject instances whose Project attribute is the current context's Project Name OR is NOT in the list of sub-projects
        # if the projectScopeUp is False and the projectScopeDown is True
        #    only capture the SearchObject instances whose Project attribute is the current context's Project Name OR is IN the list of sub-projects
        # if the projectScopeUp is True and projectScopeDown is True
        #     everything in the result is eligible so pass it on...

        if kwargs['projectScopeUp'] == True and kwargs['projectScopeDown'] == True:
            # this behavior is an intitial _gross_ approximation of recognizing the scopeUp and scopeDown settings
            # in no way should this be construed as being comprehensively accurate...
            return response

        all_search_hits = [item for item in response]
        #all_projects    = [project for project in self.getProjects()] # when this is used the projeny function is waaayyy slow...
        #                  and this is because getProjects returns _shell instances that don't have the Parent attribute.
        fields = 'ObjectID,Name,Owner,Description,Iterations,Releases,State,Parent' 
        response = self.get('Project', fetch=fields, order="Name")
        all_projects = [project for project in response]  # when this is used, projeny zips along, as each instance has Parent attribute
        current_project = self.getProject()

        project_matches = [so for so in all_search_hits if so.Project == current_project.Name]
        filtered = project_matches

        if kwargs['projectScopeUp']:
            ancestors = projectAncestors(current_project, all_projects, [])
            scope_up_matches   = [so for so in all_search_hits if so.Project in ancestors]
            filtered += scope_up_matches
        else:  # projectScopeUp is False 
            pass

        if kwargs['projectScopeDown']:
            descendents = projectDescendants(current_project, all_projects)
            scope_down_matches = [so for so in all_search_hits if so.Project in descendents and so.Project != current_project.Name]
            filtered += scope_down_matches
        else: # projectScopeDown is False
            pass

        # TODO: uniquify the filtered, just in case we have duplicate Project Names for Projects in the target Workspace
        return MockRallyRESTResponse(filtered)


    def getSchemaInfo(self, workspace, project=None):
        """
            Hit the schema endpoint for the given workspace name and return a dict
            based on the content[u'QueryResult'][u'Results'] chunk.
            Intended to be called out of context.py which hands this off to entity.py
            to store this off in SchemaItem instances.
        """
        # punt for now on the workspace, project parms
        # grab the OID for the currentContext workspace instead
        wksp_ref = self.contextHelper.currentWorkspaceRef()
        schema_endpoint = "%s/workspace/%s" % (self.schema_url, wksp_ref.split('/').pop())
        response = self.session.get(schema_endpoint, timeout=30)
        poorly_explained_schema_url_hash = response.request.url.split('/').pop()
        # above 'poorly_explained_schema_url_hash' is a key that can be used to retrieve this schema info again
        # and if the system hasn't changed then the hash is current and the cached results are used. Otherwise
        # Rally has to go pull the information again which could take somewhat longer.
        # We don't use it here as we don't account for the potential of a _really_ long winded process during which
        # Rally schema changes may be made.
        #print(response.content)
        return response.json()['QueryResult']['Results']


    def typedef(self, target_type):
        """
            Given the name of a target Rally type (aka entity name), return an instance
            of a SchemaItem class whose ElementName or TypePath matches the target_type value.
            NB:  The first call of this method for a valid specific target_type value results in 
                 the SchemaItem poking all of its SchemaAttribute items to retrieve their AllowedValues.
        """
        schema_item = self.contextHelper.getSchemaItem(target_type)
        if not schema_item:
            # TODO: should we actually raise an exception here?
            return None
        if not schema_item.completed:
            schema_item.complete(self.contextHelper.currentContext(), getCollection)
        return schema_item
        

    def validateAttributeNames(self, entity_name, itemData):
        """
            Given an entity_name and an itemData dict with attribute names and values,
            determine if any of the names are outright incorrect or if any need to be
            altered for correct case or if any are custom field Names that need
            to be altered to have the "c_" prefix.
        """
        entity_def = self.typedef(entity_name)
        entity_attributes = entity_def.Attributes 
##
##        print("%s attributes:")
##        for attr in entity_attributes:
##            print("  |%s|" % attr.ElementName)
##        print("")
##
        attr_forms = [(attr.ElementName, attr.ElementName.lower(), attr.Name.lower().replace(' ', '')) 
                      for attr in entity_attributes]
        #             ElementName, lower case ElementName, lower case Name
        txfmed_item_data = {}
        invalid_attrs = []
        for item_attr_name, item_attr_value in list(itemData.items()):
            eln_hits = [eln for eln, ell, anl in attr_forms if item_attr_name == eln]
            if eln_hits:  # is the item_attr_name an exact match for an Attribute.ElementName ?
                txfmed_item_data[item_attr_name] = item_attr_value
                continue

            c_eln_hits = [eln for eln, ell, anl in attr_forms if "c_%s" % item_attr_name == eln]
            if c_eln_hits:  # is  "c_" + item_attr_name an exact match for an Attribute.ElementName ?
                eln = c_eln_hits[0]
                txfmed_item_data[eln] = item_attr_value
                continue

            ell_hits = [eln for eln, ell, anl in attr_forms if item_attr_name.lower() == ell]
            if ell_hits:  # is the item_attr_name.lower() a match for Attribute.ElementName.lower() ?
                eln = ell_hits[0]
                txfmed_item_data[eln] = item_attr_value
                continue

            c_ell_hits = [eln for eln, ell, anl in attr_forms if "c_%s" % item_attr_name.lower() == ell]
            if c_ell_hits:  # is  "c_" + item_attr_name.lower() an exact match for an Attribute.ElementName ?
                eln = c_ell_hits[0]
                txfmed_item_data[eln] = item_attr_value
                continue

            anl_hits = [eln for eln, ell, anl in attr_forms if item_attr_name.lower().replace(' ','') == anl]
            if anl_hits:  # is the item_attr_name.lower().noSpaces() a match for Attribute.Name.lower() ? 
                eln = anl_hits[0]
                txfmed_item_data[eln] = item_attr_value
                continue

            invalid_attrs.append(item_attr_name) 

        if invalid_attrs:
            raise RallyAttributeNameError(", ".join(invalid_attrs))

        return txfmed_item_data
        

    def getState(self, entity, state_name):
        """
            State, (as of Sep 2012) is a Rally type (aka entity) not a String.
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
        criteria        = 'TypeDef.Name = "%s"' % entity
        ordering_fields = 'OrderIndex,ObjectID'
        response = self.get('State', fetch=True, query=criteria, order=ordering_fields, project=None)
        state_ix = {}
        for state in [item for item in response]:
            state_ix[(state.OrderIndex, state.Name)] = state
        state_keys = sorted(list(state_ix.keys()), key=itemgetter(0))
        states = [state_ix[key] for key in state_keys]
        return states


    def getAllowedValues(self, entityName, attributeName, **kwargs):
        """
            Given an entity name (usually an Artifact sub-type like Story, Defect,
            PortfolioItem/Feature, ...) and an attribute of the Artifact sub-type,
            return the list of values currently defined for that field.  
            In most cases, the expected context will be that the attributeName type
            is STATE, RATING or less expected, STRING. 
            While there are many STRING type attributes and they have allowedValues endpoints,
            most of them will return a boolean equivalent of True, making this method 
            less useful for those attributes.
            The original intent of allowedValues was to define a relatively small set of 
            values that would rarely be augmented.
        """
##
##        print("%s attribute name: %s" % (entityName, attributeName))
##
        schema_item = self.contextHelper.getSchemaItem(entityName)
        if not schema_item:
            # TODO: should we actually raise an exception here?
            return None
        if not schema_item.completed:
##
##            print("the schema_item was NOT completed, calling the complete method")
##
            schema_item.complete(self.contextHelper.currentContext(), getCollection)
        matching_attrs = [attr for attr in schema_item.Attributes 
                                if attr.ElementName == attributeName
                                or attr.ElementName == 'c_{0}'.format(attributeName)]
        if not matching_attrs:
            return None
        attribute = matching_attrs[0]
        collection_types = [type([]), type({})]
        if type(attribute.AllowedValues) == str:
            context = self.contextHelper.currentContext()
            avs = attribute.resolveAllowedValues(context, getCollection)
            if type(avs) not in collection_types:
                return [avs]
            return [av.StringValue for av in avs]

        # suggested by Scott Vitale to address issue in Rally WebServices response 
        #   (sometimes value is present, other times StringValue must be used)
        return [av.StringValue for av in attribute.AllowedValues]


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
        #   if so, and already attached to artifact (or other entity), short-circuit True
        #   if so, but not attached to artifact (or other entity), save attachment
        #   if not, create the AttachmentContent with filename content, 
        #           create the Attachment with basename for filename and ref the AttachmentContent 
        #              and supply the ref for the artifact (or other object) in the Artifact field for Attachment
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
        with open(filename, 'rb') as af:
            contents = base64.b64encode(af.read())
            # In Python 3.x, contents comes back as bytes, in order for json/encoder to be able
            # to do its job, we have to get the repr of contents (eg, b'VGldfak890b325bh')
            # and strip off the bytes quoting characters leaving value  VGldfak890b325bh
            if six.PY3: contents = repr(contents)[2:-1]
            
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
        # A special case is where the "Artifact" is actually a TestCaseResult, which is not a
        # subclass of Artifact in the Rally data model, but the WSAPI has been adjusted to permit
        # us to associate an Attachment with a TestCaseResult instance.
        if artifact:  
            attachment_info["Artifact"] = artifact.ref
            if artifact._type == 'TestCaseResult':
                del attachment_info["Artifact"]
                attachment_info["TestCaseResult"] = artifact.ref    
        
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
                print("Bypassing attachment for %s, no mime_type/ContentType setting..." % att_name)
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
        #att.Content = base64.decodestring(att_content.Content)  # maybe further txfm to Unicode ?
        att.Content = base64.decodebytes(att_content.Content)  # maybe further txfm to Unicode ?
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


    def deleteAttachment(self, artifact, filename):
        """
            Still unclear for WSAPI v2.0 if Attachment items can be deleted.
            Apparently AttachmentContent items can be deleted.
        """
        art_type, artifact = self._realizeArtifact(artifact)
        if not art_type:
            return False

        current_attachments = [att for att in artifact.Attachments]
        hits = [att for att in current_attachments if att.Name == filename]
        if not hits:
            return False

        # get the target Attachment and the associated AttachmentContent item
        attachment = hits.pop(0)
        if attachment.Content and attachment.Content.oid:
            success = self.delete('AttachmentContent', attachment.Content.oid, project=None)
            if not success:
                print("ERROR: Unable to delete AttachmentContent item for %s" % attachment.Name)
                return False

        deleted = self.delete('Attachment', attachment.oid, project=None)
        if not deleted:
            print("ERROR: Unable to delete Attachment for %s" % attachment.Name)
            return False
        remaining_attachments = [att for att in current_attachments if att.ref != attachment.ref]
        att_refs = [dict(_ref=str(att.ref)) for att in remaining_attachments]
        artifact_info = { 'ObjectID'    : artifact.ObjectID,
                          'Attachments' : att_refs,
                        }
        updated = self.update(art_type, artifact_info, project=None)
        if updated:
            return updated
        else: 
            return False


    def _realizeArtifact(self, artifact):
        """
            Helper method to identify the artifact type and to retrieve it if the 
            artifact value is a FormattedID. If the artifact is already an instance
            of a Rally entity, then all that needs to be done is deduce the art_type
            from the class name.  If the artifact argument given is neither of those 
            two conditions, return back a 2 tuple of (False, None).
            Once you have a Rally instance of the artifact, return back a 
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
        else: # the supplied artifact isn't anything we can deal with here...
            pass

        return art_type, artifact


    def rankAbove(self, reference_artifact, target_artifact):
        """
            Given a reference_artifact and a target_artifact, make a Rally WSAPI PUT call
            to .../<artifact_type>/target_artifact.oid?rankAbove=reference_artifact.ref
        """
        return self._rankRelative(reference_artifact, target_artifact, 'Above')


    def rankBelow(self, reference_artifact, target_artifact):
        """
            Given a reference_artifact and a target_artifact, make a Rally WSAPI PUT call
            to .../<artifact_type>/target_artifact.oid?rankBelow=reference_artifact.ref
        """
        return self._rankRelative(reference_artifact, target_artifact, 'Below')


    def rankToTop(self, target_artifact):
        """
            Given a target_artifact, make a Rally WSAPI PUT call
            to .../<artifact_type>/target_artifact.oid?rankTo=TOP
        """
        return self._rankTo(target_artifact, 'TOP')

    def rankToBottom(self, target_artifact):
        """
            Given a target_artifact, make a Rally WSAPI PUT call
            to .../<artifact_type>/target_artifact.oid?rankTo=BOTTOM
        """
        return self._rankTo(target_artifact, 'BOTTOM')


    def _rankRelative(self, reference_artifact, target_artifact, direction):
        """
            Given a reference_artifact and target_artifact, make a Rally WSAPI POST call
            to .../<artifact_type>/target_artifact.oid?rankXxx=reference_artifact.oid&key=xx&workspace=yyy.
            The POST also must include post data of {artifact_type:{'_ref':target_artifact.ref}}
            in spite of the fact the target artifact's oid is already part of the resource URI.  Wot??...
        """
        artifact_type = self._ensureRankItemSanity(target_artifact)
        resource = '%s/%s?&rank%s=%s' % (artifact_type, target_artifact.oid, direction, reference_artifact.ref) 
        update_item = {artifact_type:{'_ref':target_artifact.ref}}
        return self._postRankRequest(target_artifact, resource, update_item)


    def _rankTo(self, target_artifact, location):
        """
            Given a reference_artifact, make a Rally WSAPI POST call
            to .../<artifact_type>/target_artifact.oid?rankTo=TOP|BOTTOM&key=xx&workspace=yyy.
            The POST also must include post data of {artifact_type:{'_ref':target_artifact.ref}}
            in spite of the fact the target artifact's oid is already part of the resource URI.  Double wot??...
        """
        artifact_type = self._ensureRankItemSanity(target_artifact)
        resource = '%s/%s?&rankTo=%s' % (artifact_type, target_artifact.oid, location) 
        update_item = {artifact_type:{'_ref':target_artifact.ref}}
        return self._postRankRequest(target_artifact, resource, update_item)


    def _postRankRequest(self, target_artifact, resource, update_item):
        """
            Given an AgileCentral target Artifact and a resource URI (sans the self.service_url prefix)
            and a dict that serves as a "container" for the target item's _ref value,
            obtain the security token we need to post to AgileCentral, construct the
            full url along with the query string containing the workspace ref and the security token.
            POST to the resource supplying the update_item "container" and catch any
            non success status code returned from the operation.
            If the POST and parsing of the response was succesful, return the response instance.
        """
        workspace_ref = self.contextHelper.currentWorkspaceRef()
        auth_token = self.obtainSecurityToken()
        full_resource_url = "%s/%s&workspace=%s&key=%s" % (self.service_url, resource, workspace_ref, auth_token)
        payload = json.dumps(update_item)
        response = self.session.post(full_resource_url, data=payload, headers=RALLY_REST_HEADERS)
        context = self.contextHelper.currentContext()
        response = RallyRESTResponse(self.session, context, resource, response, "shell", 0)
        if response.status_code != HTTP_REQUEST_SUCCESS_CODE:
            problem = 'Unable to update the DragAndDropRank value for the target_artifact %s, %s'
            raise RallyRESTAPIError(problem % (target_artifact.FormattedID, response.errors[0]))
        return response


    def _ensureRankItemSanity(self, target_artifact, reference_artifact=None):
        """
            Ranking can only be done for an item that is an Artifact subclass.
            If a reference_artifact is supplied, it too must be an Artifact subclass instance.
        """
        class_ancestors = [cls.__name__ for cls in target_artifact.__class__.mro()]
        target_is_artifact = 'Artifact' in class_ancestors
        if not target_is_artifact:
            problem  = "Unable to change DragAndDropRank for target %s, not an Artifact"
            raise RallyRESTAPIError(problem % (target_artifact.__class__.__name__))
        if reference_artifact:
            class_ancestors = [cls.__name__ for cls in reference_artifact.__class__.mro()]
            reference_is_artifact = 'Artifact' in class_ancestors
            if not reference_is_artifact:
                problem  = "Unable to change DragAndDropRank for target %s, reference item is not an Artifact"
                raise RallyRESTAPIError(problem % (target_artifact.__class__.__name__))

        return target_artifact.__class__.__name__.lower()

####################################################################################################
