from datagouvapi.client import GouvApiClient
from datagouvapi.services.holidays.constants import API_SERVICE, API_URL, API_DATASET_ID


class HolidaysClient(GouvApiClient):
    def __init__(self, api_key=None):
        super().__init__(
            service=API_SERVICE,
            api_url=API_URL,
            dataset_id=API_DATASET_ID,
            api_key=api_key
        )
