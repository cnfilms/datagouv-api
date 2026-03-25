import pytest
import requests
from unittest.mock import patch, MagicMock


from datagouvapi.client import GouvApiClient
from datagouvapi.tools.models import GouvSearchResult


def _make_where_clause():
    return "registre in ('123456789', '342234')"


def _make_result():
    return GouvSearchResult(results=[], total_count=1)


@pytest.fixture
def client():
    return GouvApiClient(
        api_url="https://api.example.com", api_key="test"
    )


@patch("datagouvapi.client.requests.get")
def test_timeout_error(mock_get, client):
    mock_get.side_effect = requests.exceptions.Timeout()

    with pytest.raises(requests.exceptions.Timeout):
        client.get_data(params=_make_where_clause())


@patch("datagouvapi.client.requests.get")
def test_too_many_redirects(mock_get, client):
    mock_get.side_effect = requests.exceptions.TooManyRedirects()

    with pytest.raises(requests.exceptions.TooManyRedirects):
        client.get_data(params=_make_where_clause())


@patch("datagouvapi.client.requests.get")
@pytest.mark.parametrize("status_code", [404, 422, 500])
def test_http_error(mock_get, client, status_code):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        response=MagicMock(status_code=status_code)
    )
    mock_get.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        client.get_data(params=_make_where_clause())
    assert exc_info.value.response.status_code == status_code
