import locale
from typing import Optional

import requests

from datagouvapi.tools.helpers import GouvApiException, GouvApiWarning
from datagouvapi.tools.models import GouvSearchError


class GouvApiClient:
    """
    Generic client for Gouv API.

    :param api_url: URL used to call the desired opendata collection.
    :param api_key: Optional - Your API key for the given Gouv API for the ones that need one.
    :param locale_name: Optional - 'fr_FR.UTF-8' will be used.
    """

    TIMEOUT = 15

    def __init__(
        self, api_url: str, locale_name="fr_FR.UTF-8", api_key: Optional[str] = None
    ):
        self.api_url = api_url
        self.errors: list[GouvSearchError] = []
        self.warnings: list[GouvApiWarning] = []
        self.api_key = api_key
        self.locale = locale_name
        self._set_locale()
        self._compute_headers()

    def _raise(self, message: str):
        raise GouvApiException(service=self.__class__.__name__, message=message)

    def _add_warning(self, identifier: str, message: str):
        self.warnings.append(
            GouvApiWarning(
                identifier=identifier,
                message=message,
            )
        )

    def _add_error(self, message: str, params: str):
        self.errors.append(
            GouvSearchError(
                params=params,
                message=message,
            )
        )

    def _set_locale(self):
        locale.setlocale(locale.LC_TIME, self.locale)

    def _compute_headers(self): ...

    def get_data(self, **kwargs) -> dict:
        response = requests.get(url=self.api_url, timeout=self.TIMEOUT, **kwargs)
        response.raise_for_status()
        return response.json()
