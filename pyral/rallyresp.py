
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

__version__ = (0, 8, 9)

import sys
import re
from exceptions import StopIteration
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
        An instance of this class is used to wrap the response from the wellrested.JsonRestClient.
        Part of the wrapping includes an iterator based interface to the collection of records
        returned by the request (for GET).
    """

    def __init__(self, session, context, request, response, hydration, limit):
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
        self.data     = None
        self.target   = request.split('?')[0].split('.')[0]
        self.errors   = []
        self.warnings = []
        self._item_type  = None
##
##        print "resource: ", self.resource
##        print "response is a %s" % type(response)  
##        # with attributes of status_code, content, data
##        # The content is a string that needs to be turned into a json object
##        # the json dict should have a key named 'QueryResult' or 'CreateResult' or 
##        # 'DeleteResult' or 'UpdateResult' or 'OperationResult'
##
        self.status_code = response.status_code
        self.headers     = response.headers
##
##        print "RallyRESTResponse.status_code is %s" % self.status_code
##        print "RallyRESTResponse.headers: %s" % repr(self.headers)
##
##        if self.status_code == 405:
##            print "RallyRESTResponse.status_code is %s" % self.status_code
##            print response.content
##            print "x" * 80
##
        if isinstance(response, ErrorResponse):
            if 'OperationResult' in response.content:
                if 'Errors' in response.content['OperationResult']:
                    self.errors = response.content['OperationResult']['Errors']
            return

        self._stdFormat  = True
        self.content     = json.loads(response.content)
        self.request_type, self.data = self._determineRequestResponseType(request)
##
##        print "RallyRESTResponse request_type: %s" % self.request_type
##

        #if self.request_type not in ['Operation', 'Create', 'Query', 'Update', 'Delete']:
        if self.request_type == 'ImpliedQuery':
            # the request is against a Rally Type name, ie. 'Subscription', 'Workspace', 'UserProfile' etc
            # which is context dependent and has a singleton result
            target = request.split('.')[0]  # request is either like Subscription.js?fetch=xxx, or just UserProfile
            if target not in self.content.keys():
                # check to see if there is a case-insensitive match before upchucking...
                ckls = [k.lower() for k in self.content.keys()]
                if target not in ckls:
                    errout("%s\n" % response.status_code)
                    errout("%s\n" % response.content)
                    raise RallyResponseError('missing _Xx_Result specifier for target %s' % target)
                else:
                    matching_item_ix = ckls.index(target)
                    target = self.content.keys()[matching_item_ix]
                    self.target = target
            self._stdFormat = False
            # fudge in the QueryResult.Results.<target> dict keychain
            self._item_type = target
            self.data = {u'QueryResult': {u'Results' : { target: self.content[target] }}}
            self.data[u'Errors']   = self.content[target]['Errors']
            self.data[u'Warnings'] = self.content[target]['Warnings']
            del self.content[target]['Errors']    # we just snagged this and repositioned it
            del self.content[target]['Warnings']  # ditto
            self.data[u'PageSize'] = 1
            self.data[u'TotalResultCount'] = 1

        qr = self.data
        self.errors      =     qr[u'Errors']
        self.warnings    =     qr[u'Warnings']
        self.startIndex  = int(qr[u'StartIndex'])       if u'StartIndex'       in qr else 0
        self.pageSize    = int(qr[u'PageSize'])         if u'PageSize'         in qr else 0
        self.resultCount = int(qr[u'TotalResultCount']) if u'TotalResultCount' in qr else 0
        self._page = []

        if u'Results' in qr:
            self._page = qr[u'Results']
        else:
            if u'QueryResult' in qr and u'Results' in qr[u'QueryResult']:
                self._page = qr[u'QueryResult'][u'Results']
##
##        num_items = len(self._page)
##        print "initial page has %d items" % num_items
##

        if qr.get('Object', None):
            self._page = qr['Object']['_ref']

        self._servable   = self.resultCount - (self.startIndex -1) # to account for indexing starting at 1
        self._limit      = limit
        self._served     = 0
        self._curIndex   = 0
        self.hydrator    = EntityHydrator(context, hydration=hydration)
        if self.errors:
            # transform the status code to an error code if not already an error code
            self.status_code = 404 if self.status_code == 200 else self.status_code
##
##        print "RallyRESTResponse._page: %s" % self._page
##

    def _determineRequestResponseType(self, request):
        if u'OperationResult' in self.content:
            return 'Operation', self.content[u'OperationResult']
        if u'QueryResult' in self.content:
            return 'Query', self.content[u'QueryResult']
        if u'CreateResult' in self.content:
            return 'Create', self.content[u'CreateResult']
        if u'UpdateResult' in self.content:
            return 'Update', self.content[u'UpdateResult']
        if u'DeleteResult' in self.content:
            return 'Delete', self.content[u'DeleteResult']
        if '_CreatedAt' in self.content and self.content['_CreatedAt'] == 'just now':
            return 'Create', self.content
        else:
##
##            print "????? request type an ImpliedQuery?: %s" % request
##            print self.content
##            print "=" * 80
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


    def __iter__(self):
        return self

    def next(self):
        """
            Return a hydrated instance from the self.page until the page is exhausted,
            then issue another session.get(...request...) with startIndex
            of startIndex + pageSize.  raise the IteratorException when there are no more instances
            that can be manufactured (self._curIndex > self.resultCount)
        """
##
##        print "RRR for %s, stdFormat?: %s, servable: %d  limit: %d  served: %d " % \
##              (self.target, self._stdFormat, self._servable, self._limit, self._served)
##
        if (self._served >= self._servable) or (self._limit and self._served >= self._limit):
            raise StopIteration

        if self._stdFormat:
            if self._curIndex == self.pageSize:
                self._page[:]  = self.__retrieveNextPage()
                self._curIndex = 0
            if not self._page:
                raise StopIteration
            try:
                item = self._page[self._curIndex]
            except IndexError:
                verbiage = "Unable to access item %d (%d items served so far from a " +\
                           "container purported to be %d items in length)"
                problem = verbiage % (self._curIndex+1, self._served, self.resultCount)
                errout("ERROR: %s\n" % problem)
                self._page[:] = self.__retrieveNextPage()
                pprint(self._page[0])
                raise IndexError("RallyRESTResponse._page[%d]" % self._curIndex)
        else:  # the Response had a non-std format
##
##            print "item from page is a %s, but Response was not in std-format" % self._item_type
##
            #
            # have to stuff the item type into the item dict like it is for the _stdFormat responses
            #
            item = self._page[self._item_type]
            item_type_key = u'_type'
            if item_type_key not in item:
                item[item_type_key] = unicode(self._item_type) 
##
##        print " next item served is a %s" % self._item_type
##
        entityInstance = self.hydrator.hydrateInstance(item)
        self._curIndex += 1
        self._served   += 1
        return entityInstance

        
    def __retrieveNextPage(self):
        """
            Issue another session GET request after changing the start index to get the next page.
        """
        self.startIndex += self.pageSize
        nextPageUrl = re.sub('&start=\d+', '&start=%s' % self.startIndex, self.resource)
        try:
            full_resource_url = '%s/%s' % (self.context.serviceURL(), nextPageUrl)
##
##            print "full URL for next page of data:\n    %s" % full_resource_url
##
            response = self.session.get(full_resource_url)
        except Exception, msg:
            exception_type, value, traceback = sys.exc_info()
            sys.stderr.write('%s: %s\n' % (exception_type, value)) 
            sys.stderr.write(traceback)
            sys.exit(9)
            return []

        content = json.loads(response.content)
        return content[u'QueryResult'][u'Results']


    def __repr__(self):
        if self.status_code == 200 and self._page:
            try:
                entity_type = self._page[0][u'_type']
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
                         (self.req_type, self.resultCount, self.content['Results'])
            return "%s %s" % (self.status_code, blurb)

##################################################################################################

