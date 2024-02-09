#!/usr/bin/python

###################################################################################################
#
#  pyral.query_builder -  module to build Rally WSAPI compliant query clause
#
###################################################################################################

__version__ = (1, 6, 0)

import re
from   urllib.parse import quote

###################################################################################################

class RallyUrlBuilder:
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

class RallyQueryFormatter:
    CONJUNCTIONS = ['and', 'AND', 'or', 'OR']
    CONJUNCTION_PATT = re.compile(r'\s+(AND|OR)\s+', re.I | re.M)
    ATTR_IDENTIFIER = r'[\w\.]+[a-zA-Z0-9]'  # gotta be word-like possibly separated by '.' chars
    RELATIONSHIP    = r'=|!=|>|<|>=|<=|contains|!contains'
    ATTR_VALUE      = r'"[^"]+"|[^ ]+'  # double quoted value or has no leading, embedded or trailing spaces
    QUERY_CRITERIA_PATTERN = re.compile(r'^(%s) (%s) (%s)$' % (ATTR_IDENTIFIER, RELATIONSHIP, ATTR_VALUE), re.M)

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
                if cond has pattern of 'thing relation value', then urllib.parse.quote it and return it
                if cond has pattern of '(thing relation value)', then urllib.parse.quote content inside parens
                  then pass that result enclosed in parens back to the caller
            """
            first_last = f"{condition[0]}{condition[-1]}"
            if first_last == "()":
                url_encoded = quote(condition)
            else:
                url_encoded = f'({quote(condition)})' 

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
                expression = f'{field} = {tval}'
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
        # The assumption is that the caller has correctly done the parenthesized grouping
        # to end up in a binary form but we strip off the enclosing parens because the 
        # caller (RallyUrlBuilder) will be immediately supplying them after the return from here.
        if criteria.count('(') > 1:
            stripped_and_plugged  = criteria.strip()[1:-1].replace(' ', '%20')
            return stripped_and_plugged

        # commented out following substitution for 1.5.0 (and beyond), as later a call to quote(criteria ...)
        # ends up url-encoding the %26 resulting in a value of %2526 which goofs things up on the back-end in Rally
        #criteria = criteria.replace('&', '%26')
        parts = RallyQueryFormatter.CONJUNCTION_PATT.split(criteria.strip())
        # adjust parts for range condition presence, coalesce parts components that have a sequence of
        #  'foo between value1', 'and', 'value2' into 'foo between value1 and value2',
        adjusted_parts = []
        temp = parts[:]
        while temp:
            if len(temp) > 2:
                if 'between ' in temp[0].lower() and temp[1].lower() == 'and' and temp[2] and ' ' not in temp[2]:
                    range_part = f'{temp[0]} {temp[1]} {temp[2]}'
                    adjusted_parts.append(range_part)
                    conj = temp[1][:]
                    temp = temp[3:] if len(temp) > 3 else []
                    # and take out 1 'and' or 'AND' conjunction from conjunctions
                    continue
            adjusted_parts.append(temp.pop(0))
        parts = adjusted_parts

##
##        print("RallyQueryFormatter parts: %s" % repr(parts))
##
        # if no CONJUNCTION is in parts, use the condition as is (simple case)
        # OR if the criteria looks like subset query or a range query
        conjunctions = [p for p in parts if p in RallyQueryFormatter.CONJUNCTIONS]
        #if not conjunctions or re.search(r'!?between .+\s+and\s+', criteria, flags=re.I):
        if not conjunctions and re.search(r'^[\w\.0-9]+\s+!?between .+\s+and\s+.+$', criteria, flags=re.I):
            attr_ident   = r'[\w\.]+[a-zA-Z0-9]'
            # Is this a subset expression, foo in baz,korn  or foo !in burgers,fries,toast
            mo = re.search(r'^(%s)\s+(!?in)\s+(.+)$' % attr_ident, criteria, flags=re.I)
            if mo:
                attr_name, cond, values = mo.group(1), mo.group(2), mo.group(3)
                # Rally WSAPI supports attr_name in value1,value2,...  directly but not so with !in
                if cond.lower() == '!in':   # we must construct an OR'ed express with != for each listed value
                    # Rally WSAPI supports attr_name in value1,value2,...  directly but not so with !in
                    criteria = RallyQueryFormatter.constructSubsetExpression(attr_name, cond, values)
            else:
                # Is this a range expression,  someDate between today and nextYear
                mo = re.search(r'^(%s)\s+(!?between)\s+(.+)\s+and\s+(.+)$' % attr_ident, criteria, flags=re.I)
                if mo:
                    attr_name, cond, lesser, greater = mo.group(1), mo.group(2), mo.group(3), mo.group(4)
                    criteria = RallyQueryFormatter.constructRangefulExpression(attr_name, cond, lesser, greater)

            expression = quote(criteria.strip()).replace('%28', '(').replace('%29', ')')
            return expression

        parts = RallyQueryFormatter.validatePartsSyntax(parts)
        binary_expression = quote(parts.pop())
        while parts:
            item = parts.pop()
            if item in RallyQueryFormatter.CONJUNCTIONS:
                conj = item
                binary_expression = "%s (%s)" % (conj, binary_expression)
            else:
                cond = quote(item)
                binary_expression = "(%s) %s" % (cond, binary_expression)

        encoded_parened_expression = binary_expression.replace('%28', '(').replace('%29', ')')
##
##        print("RallyQueryFormatter.encoded_parened_expression: |{0}|".format(encoded_parened_expression))
##        print("=============================================================")
##
        final_expression = encoded_parened_expression.replace(' ', '%20')
        return final_expression

    @staticmethod
    def validatePartsSyntax(parts):
        attr_ident   = r'[\w\.]+[a-zA-Z0-9]'
        relationship = r'=|!=|>|<|>=|<=|contains|!contains'
        attr_value   = r'"[^"]+"|[^" ]+'
        criteria_pattern       = re.compile(r'^(%s) (%s) (%s)$'         % (attr_ident, relationship, attr_value))
        quoted_value_pattern   = re.compile(r'^(%s) (%s) ("[^"]+")$'    % (attr_ident, relationship))
        unquoted_value_pattern = re.compile(r'^(%s) (%s) ([^"].+[^"])$' % (attr_ident, relationship))
        subset_pattern         = re.compile(r'^(%s)\s+(!?in)\s+(.+)$'   %  attr_ident, flags=re.I)
        range_pattern          = re.compile(r'^(%s)\s+(!?between)\s+(.+)\s+and\s+(.+)$' % attr_ident, flags=re.I)

        valid_parts = []
        front = ""
        while parts:
            part = "%s%s" % (front, parts.pop(0))

            mo = subset_pattern.match(part)
            if mo:
                attr_name, cond, values = mo.group(1), mo.group(2), mo.group(3)
                # Rally WSAPI supports attr_name in value1,value2,...  directly,  but not so with !in
                if cond.lower() == 'in':
                    valid_parts.append(part)
                else: # we must construct an OR'ed express with != for each listed value
                    criteria = RallyQueryFormatter.constructSubsetExpression(attr_name, cond, values)
                    valid_parts.append(criteria)
                continue

            mo = range_pattern.match(part)
            if mo:
                attr_name, cond, lesser, greater = mo.group(1), mo.group(2), mo.group(3), mo.group(4)
                criteria = RallyQueryFormatter.constructRangefulExpression(attr_name, cond, lesser, greater)
                valid_parts.append(criteria)
                continue

            if criteria_pattern.match(part):
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

    #
    # subset and range related ops for building queries
    #
    @staticmethod
    def constructSubsetExpression(field, relation, values):
        """
            intended for use when a subset operator (in or !in) is in play
            State in Defined, Accepted, Relased
               needs an ORed expression ((f = D OR f = A) OR ((f = R)))
            State !in Working, Fixed, Testing
               needs an ANDed expression ((f != W AND f != F) AND ((f != T)))
        """
        operator, conjunction = "=", 'OR'
        if relation.lower() == '!in':
            operator = "!="
            conjunction = 'AND'
        if isinstance(values, str):
            if values.count(',') == 0:   # no commas equal only 1 value considered, put it in a list
                values = [values]
            else:
                values = [item.lstrip().rstrip() for item in values.split(',')]
        if len(values) == 1:
            return f'{field} {operator} "{values[0]}"'
        val1, val2 = values[:2]
        binary_expression = f'({field} {operator} "{val1}") {conjunction} ({field} {operator} "{val2}")'
        for value in values[2:]:
            binary_expression = f'({binary_expression}) {conjunction} ({field} {operator} "{value}")'
        return binary_expression

    @staticmethod
    def constructRangefulExpression(attr_name, cond, lesser, greater):
        """
            intended for use when a range operator (between or !between) is in play
            DevPhase between 2021-05-23 and 2021-07-09
               needs a single ANDed expression  ((dp >= d1) AND (dp <= d1)))
            DevPhase !between 2021-12-19 and 2022-01-03
               needs a single ORed expression  ((dp < d1) OR (dp > d1)))
        """
        rlns = ['>=', '<='] if cond.lower() == 'between' else ['<', '>']
        conjunction= 'AND'  if cond.lower() == 'between' else 'OR'
        lcond = '%s %s %s' % (attr_name, rlns[0], lesser)
        gcond = '%s %s %s' % (attr_name, rlns[1], greater)
        expression = "(%s) %s (%s)" % (lcond, conjunction, gcond)
        return expression

##################################################################################################
