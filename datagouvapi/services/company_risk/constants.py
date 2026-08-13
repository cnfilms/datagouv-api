API_VERSION = "v2.1"
API_DATASET_ENDPOINT = "catalog/datasets/annonces-commerciales/records"
API_URL = f"https://bodacc-datadila.opendatasoft.com/api/explore/{API_VERSION}/{API_DATASET_ENDPOINT}"
MANDATORY_FIELDS = ["id", "registre", "dateparution", "jugement"]

API_SEARCH_PARAMS = {
    "select": ", ".join(MANDATORY_FIELDS),
    "refine": 'familleavis_lib:"Procédures collectives"',
    "refine": "typeavis:annonce",
}
BASE_WHERE_CLAUSE = (
    "("
    # Ouverture de RJ ou de LJ
    "("
    '(jugement like "%ouverture%" OR jugement like "%prononçant%") AND '
    '(jugement like "%redressement%" OR jugement like "%liquidation%") AND '
    'not (jugement like "%rejet%") AND '
    'not (jugement like "%extension%") AND '
    'not (jugement like "%clôture%")'
    ") OR "
    # Conversion de plan autre en RJ
    "("
    'jugement like "%conversion%" AND '
    'not (jugement like "%liquidation%") AND '
    'jugement like "%redressement%"'
    ") OR "
    # Conversion de RJ en LJ
    "("
    'jugement like "%conversion%" AND '
    'jugement like "%liquidation%"'
    ") OR "
    # Résolution RJ et liquidation (formulation différente, effet identique à la conversion)
    "("
    'jugement like "%résolution%" AND '
    'jugement like "%redressement%" AND '
    'jugement like "%liquidation%"'
    ") OR "
    # Annulation / résolution du RJ sans liquidation (retour à la normale)
    "("
    '(jugement like "%annulation%" OR jugement like "%résolution%") AND '
    'jugement like "%redressement%" AND '
    'not (jugement like "%liquidation%")'
    ") OR "
    # Rectification d'erreur ; à remonter en cas de changement de status
    "("
    'jugement like "%erreur%" AND '
    'jugement like "%materielle%"'
    ") OR "
    # Clôture pour extinction du passif (retour à la normale)
    "("
    'jugement like "%clôture%" AND '
    'jugement like "%extinction%" AND '
    'jugement like "%passif%"'
    ")"
    ")"
)

MAX_BATCH_SIZE = 140
BATCH_SIZE_ERROR = (
    f"Batch size cannot be more than {MAX_BATCH_SIZE} ; HTTP request will be rejected"
)
DATE_FORMATS = ["%Y-%m-%d", "%d %B %Y"]
