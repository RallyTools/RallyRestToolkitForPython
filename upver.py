#!/usr/local/bin/python2.7

###############################################################################
#
# upver - script to up the version of the pyral package
#
USAGE = """
Usage: upver.py [--clean] x.y.z
       --clean option removes any target_file.bkp (use prior to a commit)
"""
###############################################################################

import sys, os
import re
from shutil import copyfile, move
import inspect

###############################################################################

ELEMENTS_WITH_VERSION_IDENTITIERS = """

in README.rst:
      $ python
      Python 2.7.5 [other Python interpreter info elided ...]
      >> import requests
      >> import pyral
      >> pyral.__version__
      (1, 1, 0)

in build_dist.py:
VERSION      = "1.1.0"


in setup.py:
VERSION       = '1.1.0'

modifies version identifier in all pyral/*.py files

in doc/source/conf.py:
# The short X.Y version.
version = '1.1.0'
# The full version, including alpha/beta/rc tags.
release = '1.1.0'

       assumes invocation is done in the base directory of the pyral dev tree
"""
FILE_VERSION_LOC = [
      ('README.rst'                ,  r'^The most recent release of pyral \((\d\.\d+\.\d+)\) has been tested'), 
      ('README.rst'                ,  r'^\s+>> pyral.__version__\n\s+\((\d, \d+, \d+)\)'), 
      ('README.short'              ,  r'^The most recent release of pyral \((\d\.\d+\.\d+)\) has been tested'),
      ('build_dist.py'             ,  r'^VERSION\s+= "(\d\.\d+\.\d+)"'),
      ('setup.py'                  ,  r'^VERSION\s+= \'(\d\.\d+\.\d+)\''),
      ('pyral/__init__.py'         ,  r'^__version__ = \((\d, \d+, \d+)\)'),
      ('pyral/config.py'           ,  r'^__version__ = \((\d, \d+, \d+)\)'),
      ('pyral/context.py'          ,  r'^__version__ = \((\d, \d+, \d+)\)'),
      ('pyral/entity.py'           ,  r'^__version__ = \((\d, \d+, \d+)\)'),
      ('pyral/hydrate.py'          ,  r'^__version__ = \((\d, \d+, \d+)\)'),
      ('pyral/query_builder.py'    ,  r'^__version__ = \((\d, \d+, \d+)\)'),
      ('pyral/rallyresp.py'        ,  r'^__version__ = \((\d, \d+, \d+)\)'),
      ('pyral/restapi.py'          ,  r'^__version__ = \((\d, \d+, \d+)\)'),
      ('pyral/search_utils.py'     ,  r'^__version__ = \((\d, \d+, \d+)\)'),
      ('doc/source/conf.py'        ,  r'^# The short X\.Y version\.\nversion = \'(\d\.\d+\.\d+)\'\n'),
      ('doc/source/conf.py'        ,  r'^# The full version, including alpha.*? tags\.\nrelease = \'(\d\.\d+\.\d+)\'')
    ]

###############################################################################

def main(args):
    cleanup = False
    if args[0] == "--clean":
        cleanup = True

    filenames = set([filename for filename, rx in FILE_VERSION_LOC])

    if cleanup:
        for filename in filenames:
            bkp_file = "%s.bkp" % filename
            if os.path.exists(bkp_file):
                os.remove(bkp_file)
        print("target bkp files have been washed away")
        sys.exit(0)

    for filename in filenames:
        bkp_file = "%s.bkp" % filename
        if not os.path.exists(bkp_file):
            copyfile(filename, bkp_file)

    major, minor, patch = args[0].split('.')
    for filename, regex_pattern in FILE_VERSION_LOC:
        process_for_version_update(filename, regex_pattern, major, minor, patch)

###############################################################################

def process_for_version_update(filename, regex_pattern, major, minor, patch):
    print("")
    print(filename)
    print("     %s" % regex_pattern)
    print("")

    with open(filename, 'r') as inf:
        content = inf.read()

    if r'\n' in regex_pattern:  # this is a multiline pattern
        mo = re.search(regex_pattern, content, re.M)
        if not mo:
            print("NO regex match, skipping")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            return

        updated_content = update_multiline_target(content, mo, major, minor, patch)
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

    else:  # the pattern is for a single line
        lines = content.split("\n")
        hits = [(ix, line) for ix, line in enumerate(lines) if re.search(regex_pattern, line)]
        if not hits:
            print("NO regex match, skipping")
            print("---------------------------------------------------")
            return

        hit_line = hits.pop(0)
        updated_content = update_target_hitline(lines, hit_line, regex_pattern, major, minor, patch)
        print("+++++++++++++++++++++++++++++++++++++++++++++++++++")

    upd_filename = "%s.upd" % filename
    with open(upd_filename, 'w') as updf:
        updf.write(updated_content)
    move(upd_filename, filename)

###############################################################################

def upversion(target, major, minor, patch):
    if target.count('.'):
        return ".".join([major, minor, patch])

    sep_chars = ", "
    if target.count(', '):
        sep_chars = ", "
    elif target.count(','):
        sep_chars = ","
    upped = sep_chars.join([major, minor, patch])
    return upped

###############################################################################

def update_target_hitline(lines, hit_line, regex_pattern, major, minor, patch):
    ix, hit = hit_line
    print("target line:")
    print(hit)
    mo = re.search(regex_pattern, hit)
    target = mo.groups()[0]
    upped = upversion(target, major, minor, patch)
    upped_line = hit.replace(target, upped)
    print("\nupped line:\n%s" % upped_line)
    lines[ix] = upped_line
    updated_content = "\n".join(lines)
    return updated_content
        
###############################################################################

def update_multiline_target(content, mo, major, minor, patch):
    #dumpit(mo)
    before = content[:mo.start()]
    after  = content[mo.end():]
    block  = mo.group()
    print("target block:\n%s" % block)
    target = mo.groups()[0]
    print(target)
    upped = upversion(target, major, minor, patch)
    upped_block = block.replace(target, upped)
    print("\nupped block:\n%s" % upped_block)
    updated_content = before + upped_block + after
    return updated_content

###############################################################################

def dumpit(mo):
    """
    'string',
    'start', 
    'end', 
    'pos', 
    'endpos', 
    'expand', 
    'group',
    'groupdict', 
    'groups', 
    'lastgroup', 
    'lastindex', 
    're', 
    'regs', 
    'span', 
    """
    #guts = inspect.getmembers(mo)
    #for attr_name, value in guts:
    #    if attr_name[:2] != '__':
    #        print("%s: %s" % (attr_name, value))
    #        print("")
    print("===========================================================")
    print("%s: %s" % ('start'  , mo.start()  ))
    print("%s: %s" % ('end'    , mo.end()    ))
    #print("%s: %s" % ('regs'   , mo.regs)  )
    #print("%s: %s" % ('span'   , mo.span()   ))
    print("%s:\n%s" % ('group'  , mo.group()  ))
    span = mo.string[mo.start():mo.end()]
    print("span?:\n%s" % span)

#start: <built-in method start of _sre.SRE_Match object at 0x104dc1b90>
#end:   <built-in method end of _sre.SRE_Match object at 0x104dc1b90>
#
#regs: ((2186, 2222),)
#span: <built-in method span of _sre.SRE_Match object at 0x104dc1b90>
#
#group: <built-in method group of _sre.SRE_Match object at 0x104dc1b90>
#groups: <built-in method groups of _sre.SRE_Match object at 0x104dc1b90>
#groupdict: <built-in method groupdict of _sre.SRE_Match object at 0x104dc1b90>

###############################################################################
###############################################################################

if __name__ == "__main__":
    main(sys.argv[1:])

