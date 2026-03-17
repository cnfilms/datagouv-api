import json
import locale
from dataclasses import dataclass
from typing import Any, TypedDict, Optional

import requests

from datagouvapi.tools.constants import (TIMEOUT, DEFAULT_LOCALE, API_BASE_ENDPOINT,
                                         TOO_MANY_REDIRECTS_ERROR, TIMEOUT_ERROR, BATCH_SIZE_ERROR)
from datagouvapi.tools.helpers import GouvApiException, GouvApiWarning


class GouvSearchError(TypedDict):
    params: str
    message: str
    status_code: int

class GouvSearchResult(TypedDict):
    total_count: int
    records: list[dict[str, str]]
    errors: list[GouvSearchError]


class GouvApiClient:
    """
        Generic client for Gouv API.

        :param service: Service name that will inherit this class ; help identifying which one in errors messages.
        :param api_url: URL used to call the desired opendata api.
        :param dataset_id: Identifier of the desired opendata collection, used to generate the complete url.
        :param api_key: Optional - Your API key for the given Gouv API for the ones that need one.
        :param locale: Optional - 'fr_FR.UTF-8' will be used.

    """
    def __init__(self, service: str, api_url: str, dataset_id: str, api_key: str, locale_name=DEFAULT_LOCALE):
        self.service = service
        self.api_url = api_url
        self.errors = []
        self.warnings = []
        self.dataset_id = dataset_id
        self.api_key = api_key
        self.locale = locale_name
        self._set_locale()
        self._compute_headers()

    def _raise(self, message: str, status_code: int = None):
        raise GouvApiException(service=self.service, message=message, status_code=status_code)

    def _warn(self, identifier: str, message: str):
        self.warnings.append(GouvApiWarning(
            identifier=identifier,
            message=message,
        ))

    def _add_error(self, message: str, params: str, status_code: int = None):
        self.errors.append(GouvSearchError(
            params=params,
            message=message,
            status_code=status_code,
        ))

    @property
    def endpoint(self) -> str:
        return API_BASE_ENDPOINT.format(self.dataset_id)

    @property
    def full_url(self) -> str:
        return self.api_url + self.endpoint

    def _set_locale(self):
        locale.setlocale(locale.LC_TIME, self.locale or DEFAULT_LOCALE)

    def _compute_headers(self):
        pass

    def get_data(self, params=None):
        """
        Fetch the given API dataset with optional parameters.
        :param params: query parameters ; passed as string or body if the endpoint supports it.
        :return: endpoint response ; varies with the targetted dataset.
        """
        try:
            response = requests.get(url=self.full_url, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            self._add_error(TIMEOUT_ERROR, params)
        except requests.exceptions.TooManyRedirects:
            self._add_error(TOO_MANY_REDIRECTS_ERROR, params)
        except requests.exceptions.HTTPError as e:
            detail = e.response.text if e.response else None
            message = f"{str(e)} — {detail}" if detail else str(e)
            self._add_error(message, params, status_code=e.response.status_code)


    def merge_gouv_data(self, raw_data: list[dict[str, Any]]) -> GouvSearchResult:
        """
        For records-based datasets, merge all results in one dict. Useful when get_data is used in batches.
        :param raw_data:
        :return: GouvSearchResult
        """
        total_count = 0
        results = []
        for data in raw_data:
            total_count += data['total_count']
            results.extend(data['results'])

        return GouvSearchResult(total_count = total_count,
                                records = results,
                                errors = self.errors)