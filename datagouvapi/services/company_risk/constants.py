API_SERVICE = 'bodacc'
API_URL = 'https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/'
API_DATASET_ID = 'annonces-commerciales'
API_SEARCH_PARAMS = {
    'select': 'id, dateparution, jugement, commercant, listepersonnes, registre',
    'refine': 'familleavis_lib:"Procédures collectives"',
    'refine': 'typeavis:annonce'
}
BASE_WHERE_CLAUSE = ('(jugement like "%redressement%" OR jugement like "%liquidation%") AND'
    '(jugement like "%ouverture%" OR jugement like "%annulation%" OR '
    'jugement like "%résolution%" OR jugement like "%plan%" OR '
    'jugement like "%prorogation%" OR jugement like "%modification%" OR '
    'jugement like "%conversion%")'
)

DELAY_RECOVERY = 2 # months to compute a previsionnal end date
MAX_BATCH_SIZE = 140
BATCH_SIZE_ERROR = "Batch size cannot be more than 140 ; HTTP request will be rejected"
MANDATORY_FIELDS = ['id', 'registre', 'dateparution', 'jugement']

DATE_FORMATS = ["%Y-%m-%d", "%d %B %Y"]