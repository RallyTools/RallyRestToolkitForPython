#!/usr/bin/python

###################################################################################################
#
#  pyral.query_builder -  module to build Rally WSAPI compliant query clause
#
###################################################################################################

__version__ = (1, 2, 4)

import re
import types
import six
from   six.moves.urllib.parse import quote

###################################################################################################

class RallyUrlBuilder(object):
    """
        An instance of this class is used to collect information needed to construct a
        valid URL that can be issued in a REST Request to Rally.
        The sequence of use is to obtain a RallyUrlBuilder for a named entity, 
        provide qualifying criteria, augments, scoping criteria and any provision 
        for a pretty response, and then call build to return the resulting resource URL.
        An instance can be re-used (for the same entity) by simply re-calling the 
        specification methods with differing values and then re-calling the build method.
    """
    parts = ['fetch', 'query', 'order', 
             'workspace', 'project', 'projectScopeUp', 'projectScopeDown', 
             'pagesize', 'start', 'pretty'
            ]

    def __init__(self, entity):
        self.entity = entity

    def qualify(self, fetch, query, order, pagesize, startIndex):
        self.fetch = fetch
        self.query = query
        self.order = order
        self.pagesize   = pagesize
        self.startIndex = startIndex
        self.workspace  = None
        self.project    = None
        self.scopeUp    = None
        self.scopeDown  = None
        self.pretty     = False
            

    def build(self, pretty=None):
        if pretty:
            self.pretty = True
        
        resource = "{0}?".format(self.entity)

        qualifiers = ['fetch=%s' % self.fetch]
        if self.query:
##
##            print("RallyQueryFormatter raw query: %s" % self.query)
##
            query_string = RallyQueryFormatter.parenGroups(self.query)
##
##            print("query_string: |query=(%s)|" % query_string)
##
            qualifiers.append("query=(%s)" % query_string)
        if self.order:
            qualifiers.append("order=%s" % quote(self.order))
        if self.workspace:
            qualifiers.append(self.workspace)
        if self.project:
            qualifiers.append(self.project)
        if self.scopeUp:
            qualifiers.append(self.scopeUp)
        if self.scopeDown:
            qualifiers.append(self.scopeDown)

        qualifiers.append('pagesize=%s' % self.pagesize)
        qualifiers.append('start=%s'    % self.startIndex)

        if self.pretty:
            qualifiers.append('pretty=true')

        resource += "&".join(qualifiers)
##
##        print("RallyUrlBuilder.build: resource= %s" % resource)
##
        return resource

    def augmentWorkspace(self, augments, workspace_ref):
        wksp_augment = [aug for aug in augments if aug.startswith('workspace=')]
        self.workspace = "workspace=%s" % workspace_ref
        if wksp_augment:
            self.workspace = wksp_augment[0]

    def augmentProject(self, augments, project_ref):
        proj_augment = [aug for aug in augments if aug.startswith('project=')]
        self.project = "project=%s" % project_ref
        if proj_augment:
            self.project = proj_augment[0]

    def augmentScoping(self, augments):
        scopeUp   = [aug for aug in augments if aug.startswith('projectScopeUp=')]
        if scopeUp:
            self.scopeUp = scopeUp[0]
        scopeDown = [aug for aug in augments if aug.startswith('projectScopeDown=')]
        if scopeDown:
            self.scopeDown = scopeDown[0]

    def beautifyResponse(self):
        self.pretty = True

##################################################################################################

class RallyQueryFormatter(object):
    CONJUNCTIONS = ['and', 'AND', 'or', 'OR']
    CONJUNCTION_PATT = re.compile('\s+(AND|OR)\s+', re.I | re.M)
    ATTR_IDENTIFIER = r'[\w\.]+[a-zA-Z0-9]'
    RELATIONSHIP    = r'=|!=|>|<|>=|<=|contains|!contains'
    ATTR_VALUE      = r'"[^"]+"|[^ ]+'
    QUERY_CRITERIA_PATTERN = re.compile('^(%s) (%s) (%s)$' % (ATTR_IDENTIFIER, RELATIONSHIP, ATTR_VALUE), re.M)

    @staticmethod
    def parenGroups(criteria):
        """
            Keep in mind that Rally WSAPI only supports a binary expression of (x) op (y)
            as in "(foo) and (bar)"
            or     (foo) and ((bar) and (egg))  
            Note that Rally doesn't handle (x and y and z) directly.
            Look at the criteria to see if there are any parens other than begin and end 
            if the only parens are at begin and end, strip them and subject the criteria to our
            clause grouper and binary expression confabulator. 
            Otherwise, we'll naively assume the caller knows what they are doing, ie., they are 
            aware of the binary expression requirement.
        """
        def _encode(condition):
            """
                if cond has pattern of 'thing relation value', then urllib.quote it and return it
                if cond has pattern of '(thing relation value)', then urllib.quote content inside parens
                  then pass that result enclosed in parens back to the caller
            """
            first_last = "%s%s" % (condition[0], condition[-1])
            if first_last == "()":
                url_encoded = quote(condition)
            else:
                url_encoded = '(%s)' % quote(condition)

            # replace the %xx encodings for '=', '(', ')', '!', and double quote characters
            readable_encoded =      url_encoded.replace("%3D", '=')
            readable_encoded = readable_encoded.replace("%22", '"')
            readable_encoded = readable_encoded.replace("%28", '(')
            readable_encoded = readable_encoded.replace("%29", ')')
            readable_encoded = readable_encoded.replace("%21", '!')
            return readable_encoded
##
##        print("RallyQueryFormatter.parenGroups criteria parm: |%s|" % repr(criteria))
##
        
        if type(criteria) in [list, tuple]:
            # by fiat (and until requested by a paying customer), we assume the criteria expressions are AND'ed
            #conditions = [_encode(expression) for expression in criteria] 
            conditions = [expression for expression in criteria] 
            criteria = " AND ".join(conditions)
##
##            print("RallyQueryFormatter: criteria is sequence type resulting in |%s|" % criteria)
##

        if type(criteria) == dict:  
            expressions = []
            for field, value in list(criteria.items()):
                # have to enclose string value in double quotes, otherwise turn whatever the value is into a string
                tval = '"%s"' % value if type(value) == bytes else '%s' % value
                expression = ('%s = %s' % (field, tval))
                if len(criteria) == 1:
                    return expression.replace(' ', '%20')
                expressions.append(expression)
            criteria = " AND ".join(expressions)

        # if the caller has a simple query in the form "(something relation a_value)"
        # then return the query as is (after stripping off the surrounding parens)
        if     criteria.count('(')  == 1    and criteria.count(')')  == 1    and \
               criteria.strip()[0]  == '('  and criteria.strip()[-1] == ')':
            return criteria.strip()[1:-1].replace(' ', '%20')
       
        # if caller has more than one opening paren, summarily return the query 
        # after stripping off the opening paren at the start of the string and the 
        # closing parent at the end of the string
        # The assumption is that the caller has correctly done the parenthisized grouping 
        # to end up in a binary form but we strip off the enclosing parens because the 
        # caller (RallyUrlBuilder) will be immediately supplying them after the return from here.
        if criteria.count('(') > 1:
            stripped_and_plugged  = criteria.strip()[1:-1].replace(' ', '%20')
            return stripped_and_plugged

        criteria = criteria.replace('&', '%26')        
        parts = RallyQueryFormatter.CONJUNCTION_PATT.split(criteria.strip())
##
##        print("RallyQueryFormatter parts: %s" % repr(parts))
##
        
        # if no CONJUNCTION is in parts, use the condition as is (simple case)
        conjunctions = [p for p in parts if p in RallyQueryFormatter.CONJUNCTIONS]
        if not conjunctions:
            expression = quote(criteria.strip()).replace('%28', '(').replace('%29', ')')
##
##            print("RallyQueryFormatter.no_conjunctions: |%s|" % expression)
##
            return expression

        parts = RallyQueryFormatter.validatePartsSyntax(parts)
        binary_expression = parts.pop()
        while parts:
            item = parts.pop()
            if item in RallyQueryFormatter.CONJUNCTIONS:
                conj = item
                binary_expression = "%s (%s)" % (conj, binary_expression)
            else:
                cond = quote(item)
                binary_expression = "(%s) %s" % (cond, binary_expression)

        final_expression = binary_expression.replace('%28', '(')
        final_expression =  final_expression.replace('%29', ')')
##
##        print("RallyQueryFormatter.final_expression: |%s|" % final_expression)
##        print("==============================================")
##
        final_expression = final_expression.replace(' ', '%20')
        return final_expression

    @staticmethod
    def validatePartsSyntax(parts):
        attr_ident   = r'[\w\.]+[a-zA-Z0-9]'
        relationship = r'=|!=|>|<|>=|<=|contains|!contains'
        attr_value   = r'"[^"]+"|[^" ]+'
        criteria_pattern       = re.compile('^(%s) (%s) (%s)$'         % (attr_ident, relationship, attr_value))
        quoted_value_pattern   = re.compile('^(%s) (%s) ("[^"]+")$'    % (attr_ident, relationship))
        unquoted_value_pattern = re.compile('^(%s) (%s) ([^"].+[^"])$' % (attr_ident, relationship))

        valid_parts = []
        front = ""
        while parts:
            part = "%s%s" % (front, parts.pop(0))
            mo = criteria_pattern.match(part)
            if mo:
                valid_parts.append(part)
            elif quoted_value_pattern.match(part):
                valid_parts.append(part)
            elif unquoted_value_pattern.match(part):
                wordles = part.split(' ', 2)
                recast_part = '%s %s "%s"' % tuple(wordles)
                valid_parts.append(recast_part)
            else:
                if re.match(r'^(AND|OR)$', part, re.I):
                    valid_parts.append(part)
                else:
                    front = part + " "

        if not valid_parts:
            raise Exception("Invalid query expression syntax in: %s" % (" ".join(parts)))
        
        return valid_parts
    
##################################################################################################
