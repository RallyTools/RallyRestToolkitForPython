#!/usr/bin/env python
#################################################################################################
#
# gmr.py - exercise the connectedusers endpoint with different creds in Rally sub 209
#
USAGE = """\
Usage: python3 gmr.py <user_name> <password>
"""
#################################################################################################

import sys, os
import re
import hashlib
import base64
from requests.exceptions import Timeout

from pyral import Rally, rallyWorkset, RallyRESTAPIError

CONNECTED_USER_ENDPOINT = 'http://rally1.rallydev.com/slm/webservice/v2.x/connecteduser'

errout = sys.stderr.write

#################################################################################################

def main(args):

    user = 'yeti@rallydev.com'
    pswd = ''
    wksp = 'Alligators WRK Smoke JIRA'
    proj = 'JIRA 7.x'

    user1 = 'karl.fleming@wantsneeds.org'
    user2 = 'sally.uchongoba@needswants.com'
    users = [user1, user2]

    cloaked = hashifiedUsers(users)
    result = phoneHome(user, pswd, wksp, proj, cloaked)
    print(f"hit on connecteduser returned status of {result}")

#################################################################################################

def hashifiedUsers(user_list):
    uniq_users = []
    # hash the (user names) in the user_list
    # and put them in a comma separated string
    # then use that string as the value for the X-RallyIntegrationConnectedUsers key in the header
    # of a GET to the CONNECTED_USER_ENDPOINT
    for user_name in user_list:
        m = hashlib.sha256()
        m.update(user_name.encode('UTF-8'))
        digest_byte_array = m.digest()
        hashed_string = base64.b64encode(digest_byte_array)
        chars = "".join([chr(b) for b in hashed_string])
        hashu = chars[:40]
        uniq_users.append(hashu)
    return uniq_users

def phoneHome(user, password, workspace, project, fuzzed_user_list):
    timeout = 6
    headers = {'X-RallyIntegrationName': 'GrotonBoatDock',
               'X-RallyIntegrationVersion': '1.xy.z',
               'X-RallyIntegrationVendor': 'Rally',
               'X-RallyIntegrationStatus': 'Development',
               'X-RallyIntegrationConnectedUsers': f'{",".join(fuzzed_user_list)}'
               }
    server = 'rally1.rallydev.com'
    try:
        rally = Rally(server, user, password, workspace=workspace, project=project, isolated_workspace=True)
    except Exception as exc:
        errout(f"str(exc)\n")
        sys.exit(1)

    status = 503
    try:
        query_string = f'connectedusers={",".join(fuzzed_user_list)}'
        context, augments = rally.contextHelper.identifyContext(workspace=workspace, project=project)
        request_url = f"{CONNECTED_USER_ENDPOINT}?{query_string}"
        response = rally._getRequestResponse(context, request_url, headers)
        status = response.status_code
        print(f"get of connecteduser  = {status}")
    except Timeout as exc:
        message = str(exc)
        if 'execution expired' in str(exc):
            message = "Unable to post connector metrics, attempt exceeded maximum allotted time of 6 seconds"
        # self.failed_attempts += 1
        # if self.warnings_issued < self.warning_limit:
        #    self.logger.warning(message)
        #   self.warnings_issued +=
    except Exception as exc:
        message = str(exc)
        if 'missing _Xx_Result specifier for target connecteduser' not in message:
            errout(f"{message}\n")
        else:
            parts = message.split("\n")
            status_code = parts[1]
            status = int(status_code)
    return status

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)
