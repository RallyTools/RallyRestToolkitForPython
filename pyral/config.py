#!/usr/local/bin/python3.5

###################################################################################################
#
#  pyral.config - config and "consts" for the Rally 'pyral' package for REST API operations
#
###################################################################################################

__version__ = (1, 5, 2)

import datetime
import os
import platform
import re
import glob

###################################################################################################

PROTOCOL       = "https"
SERVER         = "rally1.rallydev.com"
WEB_SERVICE    = "slm/webservice/%s"
SCHEMA_SERVICE = "slm/schema/%s"
AUTH_ENDPOINT  = "security/authorize"
WS_API_VERSION = "v2.0"

USER_NAME = "wiley@acme.com"
PASSWORD  = "G3ronim0!"

START_INDEX  =   1
MAX_PAGESIZE = 500
MAX_ITEMS    = 1000000  # a million seems an eminently reasonable limit ...

RALLY_REST_HEADERS = \
    {
      #'X-RallyIntegrationName'     : 'Python toolkit for Rally REST API', # although syntactically this is the more correct
      'X-RallyIntegrationName'     : 'Rally REST API toolkit for Python',  # this matches the format of the other language toolkits
      'X-RallyIntegrationVendor'   : 'Broadcom / Rally',
      'X-RallyIntegrationVersion'  :       '%s.%s.%s' % __version__,
      'X-RallyIntegrationLibrary'  : 'pyral-%s.%s.%s' % __version__,
      'X-RallyIntegrationPlatform' : 'Python %s' % platform.python_version(),
      'X-RallyIntegrationOS'       : platform.platform(),
      'User-Agent'                 : 'Pyral Rally WebServices Agent',
      'Content-Type'               : 'application/json',
      'Accept-Encoding'            : 'gzip'
    }

##################################################################################################

def timestamp():
    # for now, don't worry about timezone fluff, and cut off the microseconds to become millis
    return  datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

##################################################################################################

CONFIG_SETTING_PATT     = re.compile(r'^([A-Z]+)\s*=\s*(.+)$')
RALLY_ARG_SETTING_PATT1 = re.compile(r'^--(rally[SUPW][a-z]+)=(.+)\s*$')
RALLY_ARG_SETTING_PATT2 = re.compile(r'^--([ASUPWasupw][a-z]+)=(.+)\s*$')
RALLY_CONFIG_FILE_PATT  = re.compile(r'^--(cfg|conf|config|rallyConfig)=(\S+)$')

TRUTHY_VALUES = ['t', 'true',  'y', 'yes', '1']
FALSEY_VALUES = ['f', 'false', 'n', 'no',  '0']

################################################################################

def rallyWorkset(args):
    """
        intended to supplant rallySettings as of pyral 2.0.x

        priority order of Python Rally REST API server ident, credentials, workspace/project:
          1) command line args with --rallyServer, --rallyUser, --rallyPassword, --apikey,  --workspace, --project, --ping
          2) command line arg specifying a config file --rallyConfig=<config_file_name>
                                                    or --config=<config_file_name>
                                                    or --conf=<config_file_name>
                                                    or --cfg=<config_file_name>
          3) ENV variable with location of rally-<version>.cfg --> RALLY_CONFIG
          4) current directory with rally-<version>.cfg
          5) RALLY_SERVER, RALLY_USER_NAME, RALLY_PASSWORD, APIKEY, RALLY_WORKSPACE, RALLY_PROJECT env VARS
          6) SERVER, USER_NAME, PASSWORD defined in this module

        start by priming the return values with #6 and work your way up the priority ladder
    """
    # #6
    # start with the defaults defined in this module
    server_creds = [SERVER, USER_NAME, PASSWORD, "", "default", "default"]

    def snarfSettings(targetFile, server_creds):
        """
            read the filename and look for lines containing relevant Rally settings.
            alter the server_creds list if there are entries in the file to do so.
        """
        if not os.path.exists(targetFile):
            cfg_suffixed = "%s.cfg" % targetFile
            if not os.path.exists(cfg_suffixed):
                return server_creds
            else:
                targetFile = cfg_suffixed

        try:
            cf = open(targetFile, 'r')
            for line in cf:
                mo = CONFIG_SETTING_PATT.match(line)
                if mo:
                    item, value = mo.groups()
                    if   item == 'SERVER':
                        server_creds[0] = value
                    elif item == 'USER':
                        server_creds[1] = value
                    elif item == 'PASSWORD':
                        server_creds[2] = value
                    elif item == "APIKEY" or item == "API_KEY":
                        server_creds[3] = value
                    elif item == 'WORKSPACE':
                        server_creds[4] = value
                    elif item == 'PROJECT':
                        server_creds[5] = value
            cf.close()
            sc = "%s, %s, %s, %s, %s, %s" % tuple(server_creds)
            return server_creds
        except Exception as ex:
            pass

    # #5
    # if there are environment vars, use them
    #
    for ix, name in enumerate(['RALLY_SERVER', 'RALLY_USER', 'RALLY_PASSWORD', 'APIKEY', 'RALLY_WORKSPACE', 'RALLY_PROJECT']):
        if name in os.environ:
            server_creds[ix] = os.environ[name]
            
    # #4
    # if there is a rally-<version>.cfg file in the current directory matching the WS_API_VERSION
    # load with contents of that file
    entries = glob.glob('rally-*.cfg')
    target_version_config = 'rally-%s.cfg' % WS_API_VERSION
    if entries:
        if target_version_config in entries:
            server_creds = snarfSettings(target_version_config, server_creds)
        else:
            print("Ignoring non-matching version of Rally config settings: %s (working version: %s)" % \
                  (entries.pop(), WS_API_VERSION))

    # #3
    # if there is a RALLY_CONFIG environment variable pointing to a file, load with contents of file
    config_file = os.environ.get('RALLY_CONFIG', None)
    if config_file:
        server_creds = snarfSettings(config_file, server_creds)

    # #2
    # now look at the args (from command line invocation)
    # grab any --(rallyConfig|config|conf|cfg)=<filename> args, 
    # and if filename exists attempt to load with contents therein
    for arg in args:
        mo = RALLY_CONFIG_FILE_PATT.match(arg)
        if mo:
            config_token, config_file = mo.groups()
            server_creds = snarfSettings(config_file, server_creds)

    # #1
    # now look at the args (from command line invocation)
    # grab any --rallyServer=?, --rallyUser=?, --rallyPassword=?, --rallyWorkspace=?, --rallyProject=? in args
    # grab any --server=?, --user=?, --password=?, --apikey=?, --workspace=?, --project=? --ping=?in args
    for arg in args:
        mo = RALLY_ARG_SETTING_PATT1.match(arg)
        if mo:
            item, value = mo.groups()
            if   item == 'rallyServer':
                server_creds[0] = value
            elif item == 'rallyUser':
                server_creds[1] = value
            elif item == 'rallyPassword':
                server_creds[2] = value
            #elif item = 'rallyApikey':   # enable this if we ever decide that apikey arg should ever be specified as --rallyApikey
            #    server_creds[3] = value
            elif item == 'rallyWorkspace':
                server_creds[4] = value
            elif item == 'rallyProject':
                server_creds[5] = value

        mo = RALLY_ARG_SETTING_PATT2.match(arg)
        if mo:
            item, value = mo.groups()
            if   item == 'server':
                server_creds[0] = value
            elif item == 'user':
                server_creds[1] = value
            elif item == 'password':
                server_creds[2] = value
            elif item == 'apikey' or item == 'api_key':
                server_creds[3] = value
            elif item == 'workspace':
                server_creds[4] = value
            elif item == 'project':
                server_creds[5] = value

    return server_creds

################################################################################

def rallySettings(args):
    """
        ***********  DEPRECATED   *************
        priority order of Python Rally REST API server ident, credentials, workspace/project:
          1) command line args with --rallyServer, --rallyUser, --rallyPassword, --workspace, --project
          2) command line arg specifying a config file --rallyConfig=<config_file_name>
                                                    or --config=<config_file_name>
                                                    or --conf=<config_file_name>
                                                    or --cfg=<config_file_name>
          3) ENV variable with location of rally-<version>.cfg --> RALLY_CONFIG
          4) current directory with rally-<version>.cfg
          5) RALLY_SERVER, RALLY_USER_NAME, RALLY_PASSWORD, RALLY_WORKSPACE, RALLY_PROJECT env VARS
          6) SERVER, USER_NAME, PASSWORD defined in this module

        start by priming the return values with #6 and work your way up the priority ladder
    """
    # #6
    # start with the defaults defined in this module
    server_creds = [SERVER, USER_NAME, PASSWORD, "default", "default"]

    def snarfSettings(targetFile, server_creds):
        """
            read the filename and look for lines containing relevant Rally settings.
            alter the server_creds list if there are entries in the file to do so.
        """
        if not os.path.exists(targetFile):
            cfg_suffixed = "%s.cfg" % targetFile
            if not os.path.exists(cfg_suffixed):
                return server_creds
            else:
                targetFile = cfg_suffixed

        try:
            cf = open(targetFile, 'r')
            for line in cf:
                mo = CONFIG_SETTING_PATT.match(line)
                if mo:
                    item, value = mo.groups()
                    if   item == 'SERVER':
                        server_creds[0] = value
                    elif item == 'USER':
                        server_creds[1] = value
                    elif item == 'PASSWORD':
                        server_creds[2] = value
                    elif item == 'WORKSPACE':
                        server_creds[3] = value
                    elif item == 'PROJECT':
                        server_creds[4] = value
            cf.close()
            sc = "%s, %s, %s, %s, %s" % tuple(server_creds)
            return server_creds
        except Exception as ex:
            pass

    # #5
    # if there are environment vars, use them
    #
    for ix, name in enumerate(['RALLY_SERVER', 'RALLY_USER', 'RALLY_PASSWORD', 'RALLY_WORKSPACE', 'RALLY_PROJECT']):
        if name in os.environ:
            server_creds[ix] = os.environ[name]

    # #4
    # if there is a rally-<version>.cfg file in the current directory matching the WS_API_VERSION
    # load with contents of that file
    entries = glob.glob('rally-*.cfg')
    target_version_config = 'rally-%s.cfg' % WS_API_VERSION
    if entries:
        if target_version_config in entries:
            server_creds = snarfSettings(target_version_config, server_creds)
        else:
            print("Ignoring non-matching version of Rally config settings: %s (working version: %s)" % \
                  (entries.pop(), WS_API_VERSION))

    # #3
    # if there is a RALLY_CONFIG environment variable pointing to a file, load with contents of file
    config_file = os.environ.get('RALLY_CONFIG', None)
    if config_file:
        server_creds = snarfSettings(config_file, server_creds)

    # #2
    # now look at the args (from command line invocation)
    # grab any --(rallyConfig|config|conf|cfg)=<filename> args, 
    # and if filename exists attempt to load with contents therein
    for arg in args:
        mo = RALLY_CONFIG_FILE_PATT.match(arg)
        if mo:
            config_token, config_file = mo.groups()
            server_creds = snarfSettings(config_file, server_creds)

    # #1
    # now look at the args (from command line invocation)
    # grab any --rallyServer=?, --rallyUser=?, --rallyPassword=?, --rallyWorkspace=?, --rallyProject=? in args
    # grab any --server=?, --user=?, --password=?, --workspace=?, --project=? in args
    for arg in args:
        mo = RALLY_ARG_SETTING_PATT1.match(arg)
        if mo:
            item, value = mo.groups()
            if   item == 'rallyServer':
                server_creds[0] = value
            elif item == 'rallyUser':
                server_creds[1] = value
            elif item == 'rallyPassword':
                server_creds[2] = value
            elif item == 'rallyWorkspace':
                server_creds[3] = value
            elif item == 'rallyProject':
                server_creds[4] = value

        mo = RALLY_ARG_SETTING_PATT2.match(arg)
        if mo:
            item, value = mo.groups()
            if   item == 'server':
                server_creds[0] = value
            elif item == 'user':
                server_creds[1] = value
            elif item == 'password':
                server_creds[2] = value
            elif item == 'workspace':
                server_creds[3] = value
            elif item == 'project':
                server_creds[4] = value

    return server_creds

###################################################################################################
###################################################################################################
