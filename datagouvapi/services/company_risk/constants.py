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
    '(jugement like "%redressement%" OR jugement like "%liquidation%") AND'
    '(jugement like "%ouverture%" OR jugement like "%annulation%" OR '
    'jugement like "%résolution%" OR jugement like "%plan%" OR '
    'jugement like "%prorogation%" OR jugement like "%modification%" OR '
    'jugement like "%conversion%")'
)

DELAY_RECOVERY = 2  # months to compute a previsionnal end date
MAX_BATCH_SIZE = 140
BATCH_SIZE_ERROR = (
    f"Batch size cannot be more than {MAX_BATCH_SIZE} ; HTTP request will be rejected"
)

DATE_FORMATS = ["%Y-%m-%d", "%d %B %Y"]
