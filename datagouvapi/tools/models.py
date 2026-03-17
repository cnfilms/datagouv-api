from typing import TypedDict


class GouvSearchError(TypedDict):
    params: str
    message: str


class GouvSearchResult(TypedDict):
    total_count: int
    results: list[dict[str, str]]

