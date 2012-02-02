#!/opt/local/bin/python2.6

###################################################################################################
#
#  pyral.config - config and "consts" for the Rally 'pyral' package for REST API operations
#
###################################################################################################

__version__ = (0, 8, 9)

import datetime
import os
import platform
import re
import glob

###################################################################################################

PROTOCOL       = "https"
SERVER         = "rally1.rallydev.com"
WEB_SERVICE    = "slm/webservice/%s"
WS_API_VERSION = "1.29"
JSON_FORMAT    = ".js"

USER_NAME = "wiley@acme.com"
PASSWORD  = "G3ronim0!"

PAGESIZE    = 20
START_INDEX = 1
MAX_ITEMS   = 1000000  # a million seems an eminently reasonable limit ...

RALLY_REST_HEADERS = \
    {
      'X-RallyIntegrationName'     : 'Rally REST Toolkit for Python',
      'X-RallyIntegrationVendor'   : 'Rally Software Development', 
      'X-RallyIntegrationVersion'  :       '%s.%s.%s' % __version__,
      'X-RallyIntegrationLibrary'  : 'pyral-%s.%s.%s' % __version__,
      'X-RallyIntegrationPlatform' : 'Python %s' % platform.python_version(),
      'X-RallyIntegrationOS'       : platform.platform(),
      'User-Agent'                 : 'Pyral Rally WebServices Agent',
    }

##################################################################################################

def timestamp():
    # for now, don't worry about timezone fluff, and cut off the microseconds to become millis
    return  datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

##################################################################################################

CONFIG_SETTING_PATT     = re.compile('^([A-Z]+)\s*=\s*(.+)$')
RALLY_ARG_SETTING_PATT1 = re.compile('^--(rally[SUPW][a-z]+)=(.+)\s*$')
RALLY_ARG_SETTING_PATT2 = re.compile('^--([SUPWsupw][a-z]+)=(.+)\s*$')
RALLY_CONFIG_FILE_PATT  = re.compile('^--(cfg|conf|config|rallyConfig)=(\S+)$')

################################################################################

def rallySettings(args):
    """
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
        except Exception, msg:
            pass

    # #5
    # if there are environment vars, use them
    #
    for ix, name in enumerate(['RALLY_SERVER', 'RALLY_USER', 'RALLY_PASSWORD', 'RALLY_WORKSPACE', 'RALLY_PROJECT']):
        if name in os.environ:
            server_creds[ix] = name

    # #4
    # if there is a rally-<version>.cfg file in the current directory matching the WS_API_VERSION
    # load with contents of that file
    entries = glob.glob('rally-*.cfg')
    target_version_config = 'rally-%s.cfg' % WS_API_VERSION
    if entries:
        if target_version_config in entries:
            server_creds = snarfSettings(target_version_config, server_creds)
        else:
            print "Ignoring non-matching version of Rally config settings: %s (working version: %s)" % \
                  (entries.pop(), WS_API_VERSION)

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
            config_name, config_file = mo.groups()
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

