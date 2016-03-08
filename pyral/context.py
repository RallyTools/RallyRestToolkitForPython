#!/usr/local/bin/python2.7

###################################################################################################
#
#  pyral.context - Python module for tracking Rally connection context
#
#       used by pyral.restapi
#
###################################################################################################

__version__ = (1, 1, 1)

import sys, os
import platform
import subprocess
import time
import socket
import json
import re  # we use compile, match
from pprint import pprint

# intra-package imports
from .rallyresp import RallyRESTResponse
from .entity    import processSchemaInfo, getSchemaItem
from .entity    import InvalidRallyTypeNameError, UnrecognizedAllowedValuesReference

###################################################################################################

__all__ = ["RallyContext", "RallyContextHelper"]

###################################################################################################

INITIAL_REQUEST_TIME_LIMIT =   5 # in seconds
SERVICE_REQUEST_TIME_LIMIT = 120 # in seconds

IPV4_ADDRESS_PATT  = re.compile(r'^\d+\.\d+\.\d+\.\d+$')
FORMATTED_ID_PATT  = re.compile(r'^[A-Z]{1,2}\d+$')
SCHEME_PREFIX_PATT = re.compile(r'^https?://')

##################################################################################################

class RallyRESTAPIError(Exception): pass

##################################################################################################

class RallyContext(object):

    def __init__(self, server, user, password, service_url, 
                       subscription=None, workspace=None, project=None):
        self.server      = server
        self.user        = user
        self.password    = password
        self.service_url = service_url
        self.subs_name   = subscription
        self.workspace   = workspace
        self.project     = project

    def asDict(self):
        context_dict = { 'server'  : self.server,
                         'user'    : self.user,
                         'password': self.password,
                         'service_url': self.service_url,
                       }
        if self.subs_name:
            context_dict['subscription'] = self.subs_name
        if self.workspace:
            context_dict['workspace'] = self.workspace
        if self.project:
            context_dict['project'] = self.project

        return context_dict

    def subscription(self):
        return self.subs_name

    def serviceURL(self):
        return self.service_url

    def identity(self):
        subs      = self.subs_name or 'None'
        workspace = self.workspace or 'None'
        project   = self.project   or 'None'
 
        return " | ".join([self.server, self.user or "None", self.password, subs, workspace, project])

    def __repr__(self):
        return self.identity()
        
##################################################################################################

class RallyContextHelper(object):

    def __init__(self, agent, server, user, password, ping=True):
        self.agent  = agent
        self.server = server
        self.user   = user
        self.password = password
        self.ping   = ping

        # capture this user's User, UserProfile, Subscription records to extract 
        # the workspaces and projects this user has access to (and their defaults)
        self._subs_name        = ""
        self._subs_workspaces  = []  # a list of Workspace "shell" objects
        self._workspaces       = []
        self._workspace_ref    = {}
        self._workspace_inflated = {}
        self._defaultWorkspace = None
        self._currentWorkspace = None
        self._inflated         = False

        self._projects         = {}  # key by workspace name with list of projects per workspace
        self._project_ref      = {}  # key by workspace name with dict of project_name: project_ref
        self._defaultProject   = None
        self._currentProject   = None
        self.context        = RallyContext(server, user, password, self.agent.serviceURL())
        self.defaultContext = self.context # to be updated on check call 


    def check(self, server):
        """
            Make an initial attempt to contact the Rally web server and retrieve info
            for the user associated with the credentials supplied upon instantiation.
            Raise a RallyRESTAPIError if any problem is encountered.
            Otherwise call our internal method to set some relevant default information
            from the returned response.
            This method serves double-duty of verifying that the server can be contacted
            and speaks Rally WSAPI, and establishes the default workspace and project for
            the user.
        """
##
##        print " RallyContextHelper.check starting ..."
##        sys.stdout.flush()
##
        socket.setdefaulttimeout(INITIAL_REQUEST_TIME_LIMIT)
        target_host = server

        big_proxy   = os.environ.get('HTTPS_PROXY', False)
        small_proxy = os.environ.get('https_proxy', False)
        proxy = big_proxy if big_proxy else small_proxy if small_proxy else False
        proxy_host = False
        if proxy:
            if proxy.startswith('http'):
                proxy = SCHEME_PREFIX_PATT.sub('', proxy)
            proxy_host, proxy_port = proxy.split(':')
        target_host = proxy_host or server

        if self.ping:
            reachable, problem = Pinger.ping(target_host)
            if not reachable:
                 if not problem:
                     problem = "host: '%s' non-existent or unreachable"  % target_host
                 raise RallyRESTAPIError(problem)

        # note the use of the _disableAugments keyword arg in the call
        user_name_query = 'UserName = "%s"' % self.user
##
##        print "user_name_query: |%s|" % user_name_query
##
        try:
            timer_start = time.time()
            if self.user:
                response = self.agent.get('User', fetch=True, query=user_name_query, _disableAugments=True)
            else:
                response = self.agent.get('User', fetch=True, _disableAugments=True)
            timer_stop = time.time()
        except Exception as ex:
##
            print "-----"
            print str(ex)
##
            if str(ex.args[0]).startswith('404 Service unavailable'):
                # TODO: discern whether we should mention server or target_host as the culprit
                raise RallyRESTAPIError("hostname: '%s' non-existent or unreachable" % server)
            else:
                raise 
        elapsed = timer_stop - timer_start
        if response.status_code != 200:
##
##            print "context check response:\n%s\n" % response
##            print "request attempt elapsed time: %6.2f" % elapsed
##
            if response.status_code == 401:
                raise RallyRESTAPIError("Invalid credentials")
                
            if response.status_code == 404:
                if elapsed >= float(INITIAL_REQUEST_TIME_LIMIT):
                    problem = "Request timed out on attempt to reach %s" % server
                elif response.errors and 'certificate verify failed' in response.errors[0]:
                    problem = "SSL certificate verification failed"
                elif response.errors and 'Max retries exceeded with url' in response.errors[0]:
                    problem = "Target Rally host: '%s' non-existent or unreachable" % server
                elif response.errors and 'NoneType' in response.errors[0]:
                    problem = "Target Rally host: '%s' non-existent or unreachable" % server
                else:
                    sys.stderr.write("404 Response for request\n")
                    sys.stderr.write("\n".join(response.errors) + "\n")
                    if response.warnings:
                        sys.stderr.write("\n".join(response.warnings) + "\n")
                    sys.stderr.flush()
                    problem = "404 Target host: '%s' doesn't support the Rally WSAPI" % server
            else:  # might be a 401 No Authentication or 401 The username or password you entered is incorrect.
##
##                print response.status_code
##                print response.headers
##                print response.errors
##
                if 'The username or password you entered is incorrect.' in response.errors[0]:
                    problem = "Invalid credentials"
                else:
                    error_blurb = response.errors[0][:80] if response.errors else ""
                    problem = "%s %s" % (response.status_code, error_blurb)
            raise RallyRESTAPIError(problem)
##
##        print " RallyContextHelper.check got the User info ..."
##        print "response    resource: %s" % response.resource
##        print "response status code: %s" % response.status_code
##        print "response     headers: %s" % response.headers
##        print "response      errors: %s" % response.errors
##        print "response    warnings: %s" % response.warnings
##        print "response resultCount: %s" % response.resultCount
##        sys.stdout.flush()
##
        self._loadSubscription()
        self._getDefaults(response)
        self._getWorkspacesAndProjects(workspace=self._defaultWorkspace, project=self._defaultProject)
        # TODO: slurp in all schema for the default workspace and get this into the entity.py 
        schema_info = self.agent.getSchemaInfo(self._defaultWorkspace)
        processSchemaInfo(self.getWorkspace(), schema_info)
        self.inflated = 'minimal'

    def _loadSubscription(self):
        sub = self.agent.get('Subscription', fetch=True, _disableAugments=True)
        if sub.errors:
            raise Exception(sub.errors[0])
        subscription = sub.next()
        self._subs_name = subscription.Name
        self.context.subs_name = subscription.Name
        wksp_coll_ref_base = "%s/Workspaces" % subscription._ref
        workspaces_collection_url = '%s?fetch=true&query=(State = Open)&pagesize=200&start_index=1' % wksp_coll_ref_base
        workspaces = self.agent.getCollection(workspaces_collection_url, _disableAugments=True)
        subscription.Workspaces = [wksp for wksp in workspaces]
##
##        num_wksps = len(subscription.Workspaces)
##        print "Subscription has %d active Workspaces" % num_wksps
##
        self._subs_workspaces  = subscription.Workspaces
        self._defaultWorkspace = subscription.Workspaces[0]
##
##        print "Subscription default Workspace: %s" % self._defaultWorkspace.Name
##

    def _getDefaults(self, response):
        """
            We have to circumvent the normal machinery as this is part of setting up the
            normal machinery.  So, once having obtained the User object, we grab the 
            User.UserProfile.OID value and issue a GET for that using _getResourceByOID
            and handling the response (wrapped in a RallyRESTResponse).
        """
##
##        print "in RallyContextHelper._getDefaults, response arg has:"
##        #pprint(response.data[u'Results'])
##        pprint(response.data)
##
        user = response.next()
##
##        print user.details()
##
        self.user_oid = user.oid
##
##        print " RallyContextHelper._getDefaults calling _getResourceByOID to get UserProfile info..."
##        sys.stdout.flush()
##
        upraw = self.agent._getResourceByOID(self.context, 'UserProfile', user.UserProfile.oid, _disableAugments=True) 
##
##        print " RallyContextHelper._getDefaults got the raw UserProfile info via _getResourceByOID..."
##        sys.stdout.flush()
##
        resp = RallyRESTResponse(self.agent, self.context, 'UserProfile', upraw, "full", 0)
        up = resp.data[u'QueryResult'][u'Results']['UserProfile']
##
##        print "got the UserProfile info..."
##        pprint(up)
##        print "+" * 80
##
        if up['DefaultWorkspace']:
            self._defaultWorkspace = up['DefaultWorkspace']['_refObjectName']
##
##            print "  set _defaultWorkspace to: %s" % self._defaultWorkspace
##
            self._currentWorkspace = self._defaultWorkspace
            wkspace_ref = up['DefaultWorkspace']['_ref']
        else:
            self._currentWorkspace = self._defaultWorkspace.Name
            wkspace_ref            = self._defaultWorkspace._ref
            self._defaultWorkspace = self._defaultWorkspace.Name

        if up['DefaultProject']:
            self._defaultProject  = up['DefaultProject']['_refObjectName']
            self._currentProject  = self._defaultProject
            proj_ref = up['DefaultProject']['_ref']
        else:
            self._defaultProject  = ""
            self._currentProject  = ""
            proj_ref = ""
            projects = self.agent.get('Project', fetch="Name", workspace=self._defaultWorkspace)
##
##            print projects.content
##
            if projects:
                try:
                    proj = projects.next()
                    proj_ref = proj._ref
                    self._defaultProject = proj.Name
                    self._currentProject = proj.Name
                except StopIteration:  # the default Workspace might not have any projects
                    pass
##
##        print "   Default Workspace : %s" % self._defaultWorkspace
##        print "   Default Project   : %s" % self._defaultProject
##

        if not self._workspaces:
            self._workspaces    = [self._defaultWorkspace]
        if not self._projects:
            self._projects      = {self._defaultWorkspace : [self._defaultProject]}
        if not self._workspace_ref:
            short_ref = "/".join(wkspace_ref.split('/')[-2:])  # we only need the 'workspace/<oid>' part to be a valid ref
            self._workspace_ref = {self._defaultWorkspace : short_ref}
        if not self._project_ref:
            short_ref = "/".join(proj_ref.split('/')[-2:])  # we only need the 'project/<oid>' part to be a valid ref
            self._project_ref   = {self._defaultWorkspace : {self._defaultProject : short_ref}}
        self.defaultContext = RallyContext(self.server, 
                                           self.user, 
                                           self.password,
                                           self.agent.serviceURL(),
                                           subscription=self._subs_name,
                                           workspace=self._defaultWorkspace, 
                                           project=self._defaultProject)
        self.context = self.defaultContext 
##
##        print " completed _getDefaults processing..."
##


    def currentContext(self):
        return self.context

    def setWorkspace(self, workspace_name):
##
##        print "in setWorkspace, exising workspace: %s  OID: %s" % (self._currentWorkspace, self.currentWorkspaceRef())
##
        if self.isAccessibleWorkspaceName(workspace_name):
            if workspace_name not in self._workspaces:
                self._getWorkspacesAndProjects(workspace=workspace_name)
                # TODO: also nab the schema info for this if it hasn't already been snarfed
            self._currentWorkspace = workspace_name
            self.context.workspace = workspace_name
##
##            print "  current workspace set to: %s  OID: %s" % (workspace_name, self.currentWorkspaceRef())
##
            self.resetDefaultProject()
##
##            print "  context project set to: %s" % self._currentProject
##
            try:
                # make sure that entity._rally_schema gets filled for this workspace
                # this will fault and be caught if getSchemaItem raises an Exception
                getSchemaItem(self.getWorkspace(), 'Defect')
            except Exception, msg:
                schema_info = self.agent.getSchemaInfo(self.getWorkspace())
                processSchemaInfo(self.getWorkspace(), schema_info)
        else:
            raise Exception("Attempt to set workspace to an invalid setting: %s" % workspace_name)

    def getWorkspace(self):
        """
            Return a 2 tuple of (name of the current workspace, ref for the current workspace)
        """
        return (self._currentWorkspace, self.currentWorkspaceRef())


    def isAccessibleWorkspaceName(self, workspace_name):
        """
        """
        hits = [wksp.Name for wksp in self._subs_workspaces 
                           if workspace_name == wksp.Name
                          and str(wksp.State) != 'Closed'
               ] 
        accessible = True if hits else False
        return accessible


    def getAccessibleWorkspaces(self):
        """
            fill the instance cache items if not already done, then
            return a list of (workspaceName, workspaceRef) tuples
        """
        if self._inflated != 'wide':
            self._inflated = 'wide'  # to avoid recursion limits hell
            self._getWorkspacesAndProjects(workspace='*')
            
        workspaceInfo = []
        for workspace in self._workspaces:
            if workspace in self._workspace_ref:
                wksp = [wksp for wksp in self._subs_workspaces if wksp.Name == workspace][0]
                if wksp.State != 'Closed':
                    workspaceInfo.append((workspace, self._workspace_ref[workspace]))
        return workspaceInfo

    def getCurrentWorkspace(self):
        """
            Return the name of the current workspace
        """
        return self._currentWorkspace

    def currentWorkspaceRef(self):
        """
            Return the ref associated with the current workspace if you can find one
        """
##
##        print "default workspace: %s" % self._defaultWorkspace
##        print "current workspace: %s" % self._currentWorkspace
##
        if self._currentWorkspace:
            return self._workspace_ref[self._currentWorkspace]    
        else:
            return None


    def setProject(self, project_name):
        """
            Set the current context project with the given project_name
        """
        projects = self.getAccessibleProjects(self._currentWorkspace)
        hits = [name for name, ref in projects if project_name == name]
        if hits and len(hits) == 1:
            self._currentProject = project_name
            self.context.project = project_name
        else:
            raise Exception("Attempt to set project to an invalid setting: %s" % project_name)
        
    def getProject(self):
        """
            Return a two tuple of (name of the current project, ref for the current project)
        """
        return (self._currentProject, self.currentProjectRef())

    def getAccessibleProjects(self, workspace='default'):
        """
            Return a list of (projectName, projectRef) tuples
        """
        projectInfo = []
        if workspace == 'default' or not workspace:
            workspace = self._defaultWorkspace
        elif workspace == 'current':
            workspace = self._currentWorkspace

        if workspace not in self._workspaces:  # can't return anything meaningful then...
            if self._inflated == 'wide':  # can't return anything meaningful then...
               return projectInfo
            self._getWorkspacesAndProjects(workspace=workspace)
            # check self._workspaces again...
            if workspace not in self._workspaces:
                return projectInfo
##            else:
##                print "   self._workspaces augmented, now has your target workspace"
##                sys.stdout.flush()
##
        for projName, projRef in self._project_ref[workspace].items():
            projectInfo.append((projName, projRef))
        return projectInfo

    def resetDefaultProject(self):
        """
            Get the set of current valid projects by calling 
                getAccessibleProjects(self._currentWorkspace)
            If _currentProject and _defaultProject are in set of currently valid projects,
                then merely return (_currentProject, ref for _currentProject)
            Otherwise set _defaultProject to the first project name (sorted alphabetically) 
            in the set of currently valid projects.
            if the _currentProject isn't valid at this point, reset it to the _defaultProject value
            Then return a 2 tuple of (_defaultProject, ref for the _defaultProject)
        """
        current_valid_projects = self.getAccessibleProjects(self._currentWorkspace)
        proj_names = sorted([name for name, ref in current_valid_projects])
        proj_refs  = self._project_ref[self._currentWorkspace]
        if unicode(self._defaultProject) in proj_names and unicode(self._currentProject) in proj_names:
            return (self._defaultProject, proj_refs[self._defaultProject])

        if unicode(self._defaultProject) not in proj_names:
            self._defaultProject = proj_names[0]
        if unicode(self._currentProject) not in proj_names:
            self.setProject(self._defaultProject)
        return (self._defaultProject, proj_refs[self._defaultProject])


    def currentProjectRef(self):
        """
            Return the ref associated with the project in the currently selected workspace.
            If there isn't a currently selected workspace, return an empty string.
        """
        if not self._currentWorkspace:
            return ""
        if not self._currentProject:
            return ""

##
##        print " currentProjectRef() ... "
##        print "    _currentWorkspace: '%s'"  % self._currentWorkspace
##        print "    _currentProject  : '%s'"  % self._currentProject
##        print "    _project_ref keys: %s" %  repr(self._project_ref.keys())
##

        #
        # this next condition could be True in limited circumstances, like on initialization
        # when info for the _currentProject hasn't yet been retrieved,
        # which will be manifested by the _currentWorkspace not having an entry in _project_ref
        #
        if self._currentWorkspace not in self._project_ref:
            return ""
            
        proj_refs = self._project_ref[self._currentWorkspace]
        if self._currentProject in proj_refs:
            return proj_refs[self._currentProject]
        else:
            return ""

    def _establishContext(self, kwargs):
        workspace = None
        project   = None
        if kwargs and 'workspace' in kwargs:
            workspace = kwargs['workspace']
        if kwargs and 'project' in kwargs:
            project = kwargs['project']
##
##        print "_establishContext calling _getWorkspacesAndProjects(workspace=%s, project=%s)" % (workspace, project)  
##
        self._getWorkspacesAndProjects(workspace=workspace, project=project)
        if workspace:
            self._inflated = 'minimal'

    def identifyContext(self, **kwargs):
        """
            Look for workspace, project, projectScopeUp, projectScopeDown entries in kwargs.
            If present, check cache for values to provide for hrefs.
            Return back a tuple of (RallyContext instance, augment list with hrefs)
        """
##
##        print "... RallyContextHelper.identifyContext kwargs: %s" % repr(kwargs)
##        sys.stdout.flush()
##
        augments = []

        if '_disableAugments' in kwargs:
            return self.context, augments

        if not self._inflated:
            self._inflated = 'minimal'  # to avoid recursion limits hell
            self._establishContext(kwargs)

        workspace = None
        if 'workspace' in kwargs and kwargs['workspace']:
            workspace = kwargs['workspace']
            eligible_workspace_names = [wksp.Name for wksp in self._subs_workspaces]

            if workspace not in eligible_workspace_names:
                problem = 'Workspace specified: "%s" not accessible with current credentials'
                raise RallyRESTAPIError(problem % workspace)
            if workspace not in self._workspaces and self._inflated != 'wide':  
                ec_kwargs = {'workspace' : workspace}
                self._establishContext(ec_kwargs)
                self._inflated = 'narrow'

            wks_ref = self._workspace_ref[workspace]
            augments.append("workspace=%s" % wks_ref)
            self.context.workspace = workspace

        project = None        
        if 'project' in kwargs:
            if not kwargs['project']:
                self.context.project = None
                return self.context, augments

            project = kwargs['project']
            wks = workspace or self._currentWorkspace or self._defaultWorkspace
            if project not in self._projects[wks]:
                problem = 'Project specified: "%s" (in workspace: "%s") not accessible with current credentials' % \
                           (project, workspace)
                raise RallyRESTAPIError(problem)

            prj_ref = self._project_ref[wks][project]
            augments.append("project=%s" % prj_ref)
            self.context.project = project

        if 'projectScopeUp' in kwargs:
            projectScopeUp = kwargs['projectScopeUp']
            if projectScopeUp not in [0, False, 'false', 'False']:
                augments.append("projectScopeUp=true")
            else:
                augments.append("projectScopeUp=false")

        if 'projectScopeDown' in kwargs:
            projectScopeDown = kwargs['projectScopeDown']
            if projectScopeDown not in [1, True, 'true', 'True']:
                augments.append("projectScopeDown=false")
            elif projectScopeDown in [0, False, 'false', 'False']:
                augments.append("projectScopeDown=true")

        if not workspace and project:
            self.context = self.defaultContext

        return self.context, augments


    def _getWorkspacesAndProjects(self, **kwargs):
        """
        """
        target_workspace = self._currentWorkspace or self._defaultWorkspace
        if kwargs:
            if 'workspace' in kwargs and kwargs['workspace']:
                target_workspace = kwargs['workspace']
                if target_workspace == '*':  # wild card value to specify all workspaces
                    target_workspace = None
##    
##        print "in _getWorkspacesAndProjects(%s)" % repr(kwargs)
##        print "_getWorkspacesAndProjects, target_workspace: %s" % target_workspace
##        print "_getWorkspacesAndProjects, self._currentWorkspace: %s" % self._currentWorkspace
##        print "_getWorkspacesAndProjects, self._defaultWorkspace: %s" % self._defaultWorkspace
##    
            
        for workspace in self._subs_workspaces:
            # short-circuit issuing any WS calls if we don't need to 
            if target_workspace and workspace.Name != target_workspace:
                continue  
            if self._workspace_inflated.get(workspace.Name, False) == True:
                continue
##
##            print workspace.Name, workspace.oid
##
            # fill out self._workspaces and self._workspace_ref
            if workspace.Name not in self._workspaces:
                self._workspaces.append(workspace.Name)
            # we only need the 'workspace/<oid>' fragment to qualify as a valid ref
            self._workspace_ref[workspace.Name] = '/'.join(workspace._ref.split('/')[-2:])
            self._projects[     workspace.Name] = []
            self._project_ref[  workspace.Name] = {}
            resp = self.agent._getResourceByOID( self.context, 'workspace', workspace.oid, _disableAugments=True)
            response = json.loads(resp.content)
            # If SLM gave back consistent responses, we could use RallyRESTResponse, but no joy...
            # Carefully weasel into the response to get to the guts of what we need
            # and note we specify only the necessary fetch fields or this query takes a *lot* longer...
            base_proj_coll_url = response['Workspace']['Projects'][u'_ref']
            projects_collection_url = '%s?fetch="ObjectID,Name,State"&pagesize=200&start_index=1' % base_proj_coll_url
            response = self.agent.getCollection(projects_collection_url, _disableAugments=True)
#not-as-bad?#            response = self.agent.get('Project', fetch="ObjectID,Name,State", workspace=workspace.Name)

##
##            print "  Number of Projects: %d" % response.data[u'TotalResultCount']
##            for item in response.data[u'Results']:
##                print "    %-36.36s" % (item[u'_refObjectName'], )
##
            for project in response:
                projName = project.Name
                # we only need the project/123534 section to qualify as a valid ref
                projRef = '/'.join(project.ref.split('/')[-2:])
                if projName not in self._projects[workspace.Name]:
                    self._projects[   workspace.Name].append(projName)
                    self._project_ref[workspace.Name][projName] = projRef
            self._workspace_inflated[workspace.Name] = True

            if target_workspace != self._defaultWorkspace:
                if 'workspace' in kwargs and kwargs['workspace']:
                    self._inflated = 'narrow'
##
##                    print "setting _inflated to 'narrow'"
##
                else:
                    self._inflated = 'wide'
##
##                    print "setting _inflated to 'wide'"
##

    def getSchemaItem(self, entity_name):
        return getSchemaItem(self.getWorkspace(), entity_name)
        

    def __repr__(self):
        items = []
        items.append('%s = %s' % ('server',             self.server))
        items.append('%s = %s' % ('defaultContext',     self.defaultContext))
        items.append('%s = %s' % ('_subs_name',         self._subs_name))
        items.append('%s = %s' % ('_workspaces',        repr(self._workspaces)))
        items.append('%s = %s' % ('_projects',          repr(self._projects)))
        items.append('%s = %s' % ('_workspace_ref',     repr(self._workspace_ref)))
        items.append('%s = %s' % ('_project_ref',       repr(self._project_ref)))
        items.append('%s = %s' % ('_defaultWorkspace',  self._defaultWorkspace))
        items.append('%s = %s' % ('_defaultProject',    self._defaultProject))
        items.append('%s = %s' % ('_currentWorkspace',  self._currentWorkspace))
        items.append('%s = %s' % ('_currentProject',    self._currentProject))
        representation = "\n".join(items)
        return representation

##################################################################################################

class Pinger(object):
    """
        An instance of this class attempts a single ping against a given target.
        Response to the ping command results in the ping method returning True,
        otherwise a False is returned
    """
    PING_COMMAND = {'Darwin'  : ["ping", "-o", "-c", "2", "-t", "2"],
                    'Unix'    : ["ping",       "-c", "2", "-w", "2"],
                    'Linux'   : ["ping",       "-c", "2", "-w", "2"],
                    'Windows' : ["ping",       "-n", "2", "-w", "2"],
                    'Cygwin'  : ["ping",       "-n", "2", "-w", "2"]
                   }

    @classmethod
    def ping(self, target):
        plat_ident = platform.system()
        if plat_ident.startswith('CYGWIN'):
            plat_ident = 'Cygwin'
        vector = Pinger.PING_COMMAND[plat_ident][:]
        vector.append(target)
        bucket = ".ping-bucket"
        result = ""
        try:
            with open(bucket, 'w') as sink:
                rc = subprocess.call(vector, stdout=sink, stderr=sink)
        except:
            stuff = sys.exc_info()
            result = stuff[1]
        finally:
            with open(bucket, 'r') as of:
                result = of.read()
            os.unlink(bucket)

        return rc == 0, result

##################################################################################################

