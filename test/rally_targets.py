
AGICEN = "rally1.rallydev.com"
PROD   = "rally1.rallydev.com"

AGICEN_USER     = "yodel@rallydev.com"
AGICEN_PSWD     = "Vistabahn"
AGICEN_NICKNAME = "Yodel"
API_KEY         = "_x6CZhqQgiist6kTtwthsAAKHtjWE7ivqimQdpP3T4"

YETI_USER    = "yeti@rallydev.com"
YETI_PSWD    = "Vistabahn"
YETI_NAME    = "Yeti"

DEFAULT_WORKSPACE = "AC WSAPI Toolkit Python"
DEFAULT_PROJECT   = "Sample Project"

NON_DEFAULT_PROJECT = "My Project"

ALTERNATE_WORKSPACE = "Kip's Playground"
ALTERNATE_PROJECT   = "Argonaut"

BOONDOCKS_WORKSPACE = 'Alligators BLD Unigrations'
BOONDOCKS_PROJECT   = 'Sandbox'

LARGE_WORKSPACE         = 'Rally'
LARGE_PROJECT_TREE_BASE = 'Rally'

PROD_USER = "kip@closedprojects.com"
PROD_PSWD = "TwinLakes55"

ACCOUNT_WITH_NO_DEFAULTS_CREDENTIALS = ('nick@denver.com', 'P@$$w0rd')

PROJECT_SCOPING_TREE  = {
    'TOP_LEVEL_PROJECT' : { 'Arctic Elevation' :
                                ['My ship is stuck and I cant get out',
                                 'Lurking under the water is 300 megatons of payback',
                                 'Narwhal beaks carry the flag of the GWN tribe',
                                 'Fear the winter, play in the summer on the floes',
                                ]
                          },
    'SUB_PROJECTS'      : { 'Aurora Borealis'  :
                                ['Wavy Green Noodles', 'Astral Shock Treatment'],
                            'Sub Arctic Conditions' :
                                ['Look at the salmon run',
                                 'Provide bears with polaroid medicine',
                                 'The wolf boy needs to howl at the moon'
                                ],
                          },
    'BOTTOM_PROJECT'    : { 'Bristol Bay Barons' :
                             ['Sealskin lap belt grinder', 'Shiny metal pieces']
                          },
}

HTTPS_PROXY = "127.0.0.1:3128"

__all__ = [AGICEN, AGICEN_USER, AGICEN_PSWD, AGICEN_NICKNAME, PROD,
           DEFAULT_WORKSPACE, DEFAULT_PROJECT,
           NON_DEFAULT_PROJECT, ALTERNATE_WORKSPACE, ALTERNATE_PROJECT, HTTPS_PROXY]
