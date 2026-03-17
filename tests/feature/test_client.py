
import pytest
import requests
from unittest.mock import patch, MagicMock


from datagouvapi.client import GouvApiClient, GouvSearchResult
from datagouvapi.tools.constants import DEFAULT_LOCALE, TIMEOUT_ERROR, TOO_MANY_REDIRECTS_ERROR, MAX_BATCH_SIZE
from datagouvapi.tools.helpers import GouvApiException


def _make_where_clause():
    return "registre in ('123456789', '342234')"

def _make_result():
    return GouvSearchResult(records=[],
                            total_count=1,
                            errors=[])


@pytest.fixture
def client():
    return GouvApiClient(api_url="https://api.example.com",
                         dataset_id="data",
                         service="test",
                         locale_name=DEFAULT_LOCALE,
                         api_key='test')


@patch("datagouvapi.client.requests.get")
def test_timeout_error(mock_get, client):
    mock_get.side_effect = requests.exceptions.Timeout()

    client.get_data(params=_make_where_clause())

    assert len(client.errors) == 1
    assert TIMEOUT_ERROR in client.errors[0]["message"]
    assert client.errors[0]["params"] == "registre in ('123456789', '342234')"

@patch("datagouvapi.client.requests.get")
def test_too_many_redirects(mock_get, client):
    mock_get.side_effect = requests.exceptions.TooManyRedirects()

    client.get_data(params=_make_where_clause())

    assert len(client.errors) == 1
    assert TOO_MANY_REDIRECTS_ERROR in client.errors[0]["message"]

@patch("datagouvapi.client.requests.get")
def test_http_error_404(mock_get, client):
    mock_response = MagicMock()
    mock_response.status_code = 404
    http_error = requests.exceptions.HTTPError(response=mock_response)
    mock_get.return_value.raise_for_status.side_effect = http_error

    client.get_data(params=_make_where_clause())

    assert len(client.errors) == 1
    assert client.errors[0]["status_code"] == 404

@patch("datagouvapi.client.requests.get")
def test_http_error_500(mock_get, client):
    mock_response = MagicMock()
    mock_response.status_code = 500
    http_error = requests.exceptions.HTTPError("500 Server Error: Internal Server Error", response=mock_response)
    mock_get.return_value.raise_for_status.side_effect = http_error

    client.get_data(params=_make_where_clause())

    assert len(client.errors) == 1
    assert client.errors[0]["status_code"] == 500
    assert "Internal Server Error" in client.errors[0]["message"]

@patch("datagouvapi.client.requests.get")
def test_http_error_422(mock_get, client):
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.text = "Unprocessable Entity"
    http_error = requests.exceptions.HTTPError("422 Client Error: Unprocessable Entity", response=mock_response)
    mock_get.return_value.raise_for_status.side_effect = http_error

    client.get_data(params=_make_where_clause())

    assert len(client.errors) == 1
    assert client.errors[0]["status_code"] == 422
    assert "422" in client.errors[0]["message"]
    assert "Unprocessable Entity" in client.errors[0]["message"]

@patch("datagouvapi.client.requests.get")
def test_errors_accumulate_across_batch(mock_get, client):
    mock_get.side_effect = requests.exceptions.Timeout()

    batch_params = [{f"registre in ('12345678{i}', '12345678{i+2}')"} for i in range(5)]
    for params in batch_params:
        client.get_data(params=params)

    assert len(client.errors) == 5
    assert {'message': 'Timeout error', 'params': {"registre in ('123456783', '123456785')"}, 'status_code': None} in client.errors

@patch("datagouvapi.client.requests.get")
def test_errors_keep_running_across_batch(mock_get, client):

    mock_get.side_effect = [
        requests.exceptions.Timeout(),
        MagicMock(**{"raise_for_status.return_value": None, "json.return_value": _make_result()}),
        requests.exceptions.Timeout(),
    ]

    batch_params = [{f"registre in ('12345678{i}', '12345678{i+2}')"} for i in range(3)]
    results = [client.get_data(params=params) for params in batch_params]

    assert len(client.errors) == 2
    assert {'message': 'Timeout error', 'params': {"registre in ('123456782', '123456784')"}, 'status_code': None} in client.errors
    assert results[1]['total_count'] == 1

@patch("datagouvapi.client.requests.get")
def test_success_returns_json(mock_get, client):
    mock_get.return_value.json.return_value = _make_result()
    mock_get.return_value.raise_for_status.return_value = None

    result = client.get_data(params=_make_where_clause())

    assert len(client.errors) == 0


def test_batch_size_at_limit():
    client = GouvApiClient(
        api_url="https://api.example.com",
        dataset_id="data",
        service="test",
        locale_name=DEFAULT_LOCALE,
        api_key='test',
        batch_size=140
    )
    assert client.batch_size == 140


def test_batch_size_over_limit():
    with pytest.raises(GouvApiException,
                     match="'GOUV API error on test : Batch size cannot be more than 140 ; HTTP request will be rejected'"):
        GouvApiClient(
            api_url="https://api.example.com",
            dataset_id="data",
            service="test",
            locale_name=DEFAULT_LOCALE,
            api_key='test',
            batch_size=141
        )
