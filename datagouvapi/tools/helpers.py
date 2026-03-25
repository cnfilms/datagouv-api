import unicodedata
from typing import Any

from datagouvapi.tools.models import GouvSearchResult


class GouvApiException(Exception):
    def __init__(self, service, message):
        self.service = str(service)
        self.message = message

    def __str__(self):
        return repr(f"GOUV API error on {self.service}: {self.message}")


class GouvApiWarning:
    def __init__(self, identifier: str, message: str):
        self.identifier = identifier
        self.message = message

    def __str__(self):
        return f"Record id {self.identifier} raised an error: {self.message}"


def unaccent(string):
    """Removes accents from a string"""
    text = unicodedata.normalize("NFKD", string).encode("ascii", "ignore")
    return str(text.decode("utf-8"))


def merge_gouv_data(raw_data: list[dict[str, Any]]) -> GouvSearchResult:
    """
    For records-based datasets, merge all results in one dict. Useful when get_data is used in batches.
    :param raw_data:
    :return: GouvSearchResult
    """
    total_count = 0
    results = []
    for data in raw_data:
        total_count += data["total_count"]
        results.extend(data["results"])

    return GouvSearchResult(total_count=total_count, results=results)
