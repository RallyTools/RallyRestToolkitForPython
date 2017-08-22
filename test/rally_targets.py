
AGICEN = "rally1.rallydev.com"
PROD   = "rally1.rallydev.com"

AGICEN_USER = "yeti@rallydev.com"
AGICEN_PSWD = "Vistabahn"
AGICEN_NICKNAME = "Yeti"
#API_KEY = "_ABC123DEF456GHI789JKL012MNO345PQR678STU901VWXZ"

DEFAULT_WORKSPACE    = "AC WSAPI Toolkit Python"
DEFAULT_PROJECT      = "Sample Project"
NON_DEFAULT_PROJECT  = "My Project"
ALTERNATE_WORKSPACE  = "An Alternate Workspace"
#ALTERNATE_PROJECT   = "Dynamic"
ALTERNATE_PROJECT    = "An Alternate Project"

BOONDOCKS_WORKSPACE  = 'Darwin Social Club'
BOONDOCKS_PROJECT    = 'Linoleum Blast'

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

ACCOUNT_WITH_NO_DEFAULTS_CREDENTIALS = ('mortel.e.woonded@torso00bam.com', 'T2Y*&9mm409')


HTTPS_PROXY = "127.0.0.1:3128"

__all__ = [AGICEN, AGICEN_USER, AGICEN_PSWD, AGICEN_NICKNAME, PROD,
           DEFAULT_WORKSPACE, DEFAULT_PROJECT, 
           NON_DEFAULT_PROJECT, ALTERNATE_WORKSPACE, ALTERNATE_PROJECT, 
           PROJECT_SCOPING_TREE, HTTPS_PROXY]
