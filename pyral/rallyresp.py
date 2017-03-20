
###################################################################################################
#
#  pyral.response - defines a class to hold the response info from a Rally REST operation
#                   with reasonably named accessors and an iterator interface to obtain
#                   entity instances from the results
#
#          dependencies:
#               intra-package: hydrator.EntityHydrator
#
###################################################################################################

__version__ = (1, 2, 4)

import sys
import re
import json
from pprint import pprint

from .hydrate import EntityHydrator

__all__ = ['RallyRESTResponse', 'ErrorResponse', 'RallyResponseError']

##################################################################################################

errout = sys.stderr.write

##################################################################################################

class RallyResponseError(Exception): pass
   
class ErrorResponse(object):

    SECURITY_ERROR = 'An Authentication object was not found in the SecurityContext'
    INVALID_CREDENTIALS = "Error 401 The username or password you entered is incorrect."

    def __init__(self, status_code, problem):
        self.status_code = status_code
        self.headers = {'placeholder' : True}
        self.content = {'OperationResult' : {'Errors'  : [problem],
                                             'Warnings': [],
                                             'Results' : [],
                                            }
                       }

        prob_str = str(problem) 
        if ErrorResponse.SECURITY_ERROR in prob_str:
            self.content['OperationResult']['Errors'] = [ErrorResponse.SECURITY_ERROR]

        if ErrorResponse.INVALID_CREDENTIALS in prob_str:
            self.content['OperationResult']['Errors'] = [ErrorResponse.INVALID_CREDENTIALS]

##################################################################################################

class RallyRESTResponse(object):
    """
        An instance of this class is used to wrap the response from the Rally REST endpoint.
        Part of the wrapping includes an iterator based interface to the collection of records
        returned by the request (for GET).
    """

    def __init__(self, session, context, request, response, hydration, limit, debug=False):
        """
            A wrapper for the response received back from the REST API.
            The response has status_code, headers and content attributes which will be preserved.
            In addition, we augment with some easy access attributes into the data attribute
            and provide an iterator protocol to obtain hydrated instances with information
            contained in the response['QueryResult']['Results'] list.
        """
        self.session  = session
        self.context  = context
        self.resource = request
        self.debug    = debug
        self.data     = None
        request_path_elements = request.split('?')[0].split('/')
##
##        print("RRR.init request: =  %s " % request)
##        print("RRR.init request_path_elements =  %s " % repr(request_path_elements))
##
        self.target = request_path_elements[-1]
        if re.match('^\d+$', self.target):
            self.target = request_path_elements[-2] # this happens on request for RevisionHistory
            if self.target.lower() == 'revisionhistory':
                self.target = 'RevisionHistory'

        self._served  = -1
        self.errors   = []
        self.warnings = []
        self._item_type  = self.target
##
##        print("+" * 85)
##        print("resource: ", self.resource)
##        print("response is a %s" % type(response))
##        # with attributes of status_code, content, data
##        # The content is a string that needs to be turned into a json object
##        # the json dict should have a key named 'QueryResult' or 'CreateResult' or 
##        # 'DeleteResult' or 'UpdateResult' or 'OperationResult'
##
        self.status_code = response.status_code
        self.headers     = response.headers
##
##        print("RallyRESTResponse.status_code is %s" % self.status_code)
##        print("RallyRESTResponse.headers: %s" % repr(self.headers))
##        # response has these keys: url, status_code, headers, raw, _content, encoding, reason, elapsed, history, connection
##
##        if self.status_code == 405:
##            print("RallyRESTResponse.status_code is %s" % self.status_code)
##            print(response.content)
##            print("x" * 80)
##
        if isinstance(response, ErrorResponse):
            if 'OperationResult' in response.content:
                if 'Errors' in response.content['OperationResult']:
                    self.errors = response.content['OperationResult']['Errors']
            return

        self._stdFormat  = True
        try:
            self.content = response.json()
        except:
            problem = "Response for request: {0} either was not JSON content or was an invalidly formed/incomplete JSON structure".format(self.resource)
            raise RallyResponseError(problem)
##
##        print("response content: %s" % self.content)
##
        self.request_type, self.data = self._determineRequestResponseType(request)
##
##        print("RallyRESTResponse request_type: %s for %s" % (self.request_type, self._item_type))
##

        if self.request_type == 'ImpliedQuery':
            # the request is against a Rally Type name, ie. 'Subscription', 'Workspace', 'UserProfile', etc.
            # or a Rally "sub-type" like PortfolioItem/Feature
            # which is context dependent and has a singleton result
            target = self.target 
            if target.endswith('.x'):
                target = target[:-2]
##
##            print("ImpliedQuery presumed target: |%s|" % target)
##            print("")
##
            if target not in list(self.content.keys()):
                # check to see if there is a case-insensitive match before upchucking...
                ckls = [k.lower() for k in list(self.content.keys())]
                if target.lower() not in ckls:
                    forensic_info = "%s\n%s\n" % (response.status_code, response.content)
                    problem = 'missing _Xx_Result specifier for target %s in following:' % target
                    raise RallyResponseError('%s\n%s' % (problem, forensic_info))
                else:
                    matching_item_ix = ckls.index(target.lower())
                    target = list(self.content.keys())[matching_item_ix]
                    self.target = target
            self._stdFormat = False
            # fudge in the QueryResult.Results.<target> dict keychain
            self._item_type = target
            self.data = {'QueryResult': {'Results' : { target: self.content[target] }}}
            self.data['Errors']   = self.content[target]['Errors']
            self.data['Warnings'] = self.content[target]['Warnings']
            del self.content[target]['Errors']    # we just snagged this and repositioned it
            del self.content[target]['Warnings']  # ditto
            self.data['PageSize'] = 1
            self.data['TotalResultCount'] = 1

        qr = self.data
        self.errors      =     qr['Errors']
        self.warnings    =     qr['Warnings']
        self.startIndex  = int(qr['StartIndex'])       if 'StartIndex'       in qr else 0
        self.pageSize    = int(qr['PageSize'])         if 'PageSize'         in qr else 0
        self.resultCount = int(qr['TotalResultCount']) if 'TotalResultCount' in qr else 0
        self._limit      = limit if limit > 0 else self.resultCount
        self._page = []

        if 'Results' in qr:
            self._page = qr['Results']
        else:
            if 'QueryResult' in qr and 'Results' in qr['QueryResult']:
                self._page = qr['QueryResult']['Results']
##
##        print("initial page has %d items" % len(self._page))
##

        if qr.get('Object', None):
            self._page = qr['Object']['_ref']
##
##        print("%d items in the results starting at index: %d" % (self.resultCount, self.startIndex))
##

        # for whatever reason, some queries where a start index is unspecified 
        # result in the start index returned being a 0 or a 1, go figure ...
        # so we don't adjust the _servable value unless the start index is > 1
        self._servable = 0
        if self.resultCount > 0:
           self._servable = self.resultCount
           if self.startIndex > 1:
               self._servable = self.resultCount - self.startIndex
        self._servable   = min(self._servable, self._limit)
        self._served     = 0
        self._curIndex   = 0
        self.hydrator    = EntityHydrator(context, hydration=hydration)
        if self.errors:
            # transform the status code to an error code indicating an Unprocessable Entity if not already an error code
            self.status_code = 422 if self.status_code == 200 else self.status_code
##
##        print("RallyRESTResponse, self.target: |%s|" % self.target)
##        print("RallyRESTResponse._page: %s" % self._page)
##        print("RallyRESTResponse, self.resultCount: |%s|" % self.resultCount)
##        print("RallyRESTResponse, self.startIndex : |%s|" % self.startIndex)
##        print("RallyRESTResponse, self._servable  : |%s|" % self._servable)
##        print("")
##

    def _determineRequestResponseType(self, request):
        if 'OperationResult' in self.content:
            return 'Operation', self.content['OperationResult']
        if 'QueryResult' in self.content:
            return 'Query', self.content['QueryResult']
        if 'CreateResult' in self.content:
            return 'Create', self.content['CreateResult']
        if 'UpdateResult' in self.content:
            return 'Update', self.content['UpdateResult']
        if 'DeleteResult' in self.content:
            return 'Delete', self.content['DeleteResult']
        if '_CreatedAt' in self.content and self.content['_CreatedAt'] == 'just now':
            return 'Create', self.content
        else:
##
##            print("????? request type an ImpliedQuery?: %s" % request)
##            print(self.content)
##            print("=" * 80)
##
            return 'ImpliedQuery', self.content


    def _item(self):
        """
            Special non-public method, meant to only be used from the __getattr__ method 
            where a request has been issued for a specific entity OID.  
            Return the single item or None if the status_code != 200
        """
        if self.status_code == 200:
            return self._page[0]
        else:
            return None

    def __bool__(self):
        """
            This is for evaluating any invalid response as False.
        """
        if 200 <= self.status_code < 300:
            return True
        else:
            return False

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        """
            Return a hydrated instance from the self.page until the page is exhausted,
            then issue another session.get(...request...) with startIndex
            of startIndex + pageSize.  raise the IteratorException when there are no more instances
            that can be manufactured (self._curIndex > self.resultCount)
        """
##
##        print("RallyRestResponse for %s, _stdFormat?: %s, _servable: %d  _limit: %d  _served: %d " % \
##              (self.target, self._stdFormat, self._servable, self._limit, self._served))
##
        if (self._served >= self._servable) or (self._limit and self._served >= self._limit):
            raise StopIteration

        if self._stdFormat:
## 
##            print("RallyRESTResponse.next, _stdFormat detected")
##
            if self._curIndex == self.pageSize:
                self._page[:]  = self.__retrieveNextPage()
                self._curIndex = 0
            if not self._page:
                raise StopIteration
            try:
                item = self._page[self._curIndex]
            #except IndexError:
            #    verbiage = "Unable to access item %d (%d items served so far from a " +\
            #               "container purported to be %d items in length)"
            #    problem = verbiage % (self._curIndex+1, self._served, self.resultCount)
            #    errout("ERROR: %s\n" % problem)
            #    self._page[:] = self.__retrieveNextPage()
            #    pprint(self._page[0])
            #    raise IndexError("RallyRESTResponse._page[%d]" % self._curIndex)
            except IndexError:
                item = None
                if self.target in ['Workspace', 'Workspaces', 'Project', 'Projects']:
                    try:
                        self.page[:] = self.__retrieveNextPage()
                        self._curIndex = 0
                        item = self.page[self._curIndex]
                    except:
                        exception_type, value, traceback = sys.exc_info()
                        exc_name = re.search("'exceptions\.(.+)'", str(exception_type)).group(1)
                        problem = '%s: %s for response from request to get next data page for %s' % (exc_name, value, self.target)
                        errout("ERROR: %s\n" % problem)
                if item is None:               
                    verbiage = "Unable to access item %d (%d items served so far from a " +\
                               "container purported to be %d items in length)"
                    problem = verbiage % (self._curIndex+1, self._served, self.resultCount)
                    errout("ERROR: %s\n" % problem)
                    raise StopIteration
        else:  # the Response had a non-std format
##
##            blurb = "item from page is a %s, but Response was not in std-format" % self._item_type
##            print("RallyRESTResponse.next: %s" % blurb)
##
            #
            # have to stuff the item type into the item dict like it is for the _stdFormat responses
            #
            item = self._page[self._item_type]
            item_type_key = '_type'
            if item_type_key not in item:
                item[item_type_key] = str(self._item_type) 

        del item['_rallyAPIMajor']
        del item['_rallyAPIMinor']

        if self.debug:
            self.showNextItem(item)

        entityInstance = self.hydrator.hydrateInstance(item)
        self._curIndex += 1
        self._served   += 1
##
##        print(" next item served is a %s" % entityInstance._type)
##
        return entityInstance

    def showNextItem(item):
        print(" next item served is a %s" % self._item_type)
        print("RallyRESTResponse.next, item before call to to hydrator.hydrateInstance")
        all_item_keys = sorted(item.keys())
        underscore_prefix_keys = [key for key in all_item_keys if key[0] == u'_']
        std_underscore_prefix_keys = ['_type', '_ref', '_refObjectUUID', '_CreatedAt', '_objectVersion']
        for _key in std_underscore_prefix_keys:
            try: 
                print("    %20.20s: %s" % (_key, item[_key])) 
            except: 
                pass
        other_prefix_keys = [key for key in underscore_prefix_keys if key not in std_underscore_prefix_keys]
        for _key in other_prefix_keys:
            print("    %20.20s: %s" % (_key, item[_key]))
        print("")
        regular_keys = [key for key in all_item_keys if key[0] !='_']
        std_regular_keys = ['ObjectID', 'ObjectUUID', 'CreationDate']
        for key in std_regular_keys:
            try: 
                print("    %20.20s: %s" % (key, item[key]))
            except: 
                pass
        other_regular_keys = [key for key in regular_keys if key not in std_regular_keys]
        for key in other_regular_keys:
            print("    %20.20s: %s" % (key, item[key]))
        print("+ " * 30)

        
    def __retrieveNextPage(self):
        """
            Issue another session GET request after changing the start index to get the next page.
        """
        self.startIndex += self.pageSize
        nextPageUrl = re.sub('&start=\d+', '&start=%s' % self.startIndex, self.resource)
        if not nextPageUrl.startswith('http'):
            nextPageUrl = '%s/%s' % (self.context.serviceURL(), nextPageUrl)
##
##        print("")
##        print("full URL for next page of data:\n    %s" % nextPageUrl)
##        print("")
##
        try:
            response = self.session.get(nextPageUrl)
        except Exception as ex:
            exception_type, value, traceback = sys.exc_info()
            sys.stderr.write('%s: %s\n' % (exception_type, value)) 
            sys.stderr.write(traceback)
            sys.exit(9)
            return []

        content = response.json()
        return content['QueryResult']['Results']


    def __repr__(self):
        if self.status_code == 200 and self._page:
            try:
                entity_type = self._page[0]['_type']
                return "%s result set, totalResultSetSize: %d, startIndex: %s  pageSize: %s  current Index: %s" % \
                   (entity_type, self.resultCount, self.startIndex, self.pageSize, self._curIndex)
            except:
                return "%s\nErrors: %s\nWarnings: %s\nData: %s\n" % (self.status_code, 
                                                                     self.errors,
                                                                     self.warnings,
                                                                     self._page)
        else:    
            if self.errors:
                blurb = self.errors[0]
            elif self.warnings:
                blurb = self.warnings[0]
            else:
                blurb = "%sResult TotalResultCount: %d  Results: %s" % \
                         (self.request_type, self.resultCount, self.content['QueryResult']['Results'])
            return "%s %s" % (self.status_code, blurb)

##################################################################################################

