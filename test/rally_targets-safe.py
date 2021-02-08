
RALLY = "1yllar.rallydev.com"
PROD  = "officialness.rallydev.com"

RALLY_USER = "usernumbernonei@acme.com"
RALLY_PSWD = "B1G^S3Kretz"
RALLY_NICKNAME = "Wiley"
APIKEY     = "_ABC123DEF456GHI789JKL012MNO345PQR678STU901VWXZ"

DEFAULT_WORKSPACE    = "Your Default Workspace"
DEFAULT_PROJECT      = "Your Default Project"

NON_DEFAULT_PROJECT  = "A non-default Project"

ALTERNATE_WORKSPACE  = "An Alternate Workspace"
ALTERNATE_PROJECT    = "An Alternate Project"

BOONDOCKS_WORKSPACE  = 'Darwin Social Club'
BOONDOCKS_PROJECT    = 'Linoleum Blast'

LARGE_WORKSPACE         = "Bonktorius Maximus"
LARGE_PROJECT_TREE_BASE = "Amalgamated Hoodoo"

PROD_USER = "somebody@aplace.com"
PROD_PSWD = "urSECr8He@R"

ACCOUNT_WITH_NO_DEFAULTS_CREDENTIALS = ('mortel.e.woonded@torso00bam.com', 'T2Y*&9mm409')

PROJECT_SCOPING_TREE = {
    'TOP_LEVEL_PROJECT' : {'Arctic Elevation' :
                               [ 'My ship is stuck and I cant get out!',
                                 'Lurking under the water is 300 megatons of payback',
                                 'Narwhal beaks carry the flag of the GWN tribe',
                                 'Fear the winter, play in the summer on the floes'
                               ]
                          },
    'SUB_PROJECTS'     : { 'Aurora Borealis' :
                               [ 'Wavy Green Noodles', 'Astral Shock Treatment' ],
                           'Sub Arctic Conditions' :
                               [ 'Look at the salmon run',
                                 'Provide bears with polaroid medicine',
                                 'The wolf boy needs to howl at the moon',
                               ]
                         },
    'BOTTOM_PROJECT' :   { 'Bristol Bay Barons' :
                               ['Sealskin lap belt grinder', 'Shiny metal pieces']
                         }
}

HTTPS_PROXY = "127.0.0.1:3128"
HTTPS_PROXY = "127.0.0.1:9654"

#---------------------------------------------------------------------------
# uncomment this block for entries for access to an alternate test environment
#RALLY = 'rally1.rallydev.com'
#PROD  = 'rally1.rallydev.com'
#PROD_USER = "rascal@mischief.com"
#PROD_PSWD = "StRiPeSand-D-a-s-h-e-s"
#-----------------------------------------------------------------------------------------

__all__ = [RALLY, RALLY_USER, RALLY_PSWD, RALLY_NICKNAME,
           PROD,  PROD_USER,  PROD_PSWD,
           DEFAULT_WORKSPACE, DEFAULT_PROJECT, 
           NON_DEFAULT_PROJECT, ALTERNATE_WORKSPACE, ALTERNATE_PROJECT, 
           PROJECT_SCOPING_TREE, HTTPS_PROXY]

