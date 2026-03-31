import datetime
from unittest.mock import MagicMock
from requests import exceptions
import pytest

from datagouvapi.services.company_risk.company_risk import (
    CompanyRiskClient,
    parse_date_fin_from_complement,
)
from datagouvapi.services.company_risk.constants import BATCH_SIZE_ERROR, DELAY_RECOVERY
from datagouvapi.services.company_risk.models import JudgmentEnum

MOCK_IDENTIFIERS = {
    "735580060": 2,
    "422734970": 45,
    "897572376": "897572376",
    "319439105": 5,
    "338217854": 76,
    "0832": 2344,
    "483991253": 1,
}

MOCK_SIRENS_ONLY = [
    "735580060",
    "422734970",
    "897572376",
    "319439105",
    "338217854",
    "0832",
]
MOCK_SIRETS_AS_IDENTIFIERS = {
    "735580060": "7355800600453",
    "897572376": "8975723760004",
}

MOCK_MERGED_DATA = {
    "total_count": 2,
    "results": [
        {
            "dateparution": "2019-07-21",
            "id": "4436T3",
            "jugement": '{"famille": "Jugement de clôture", "nature": "Jugement de clôture pour insuffisance d\'actif", "date": "6 may 2011", "complementJugement": "Jugement prononçant la liquidation judiciaire", "type": "initial"}',
            "registre": ["897 572 376", "897572376"],
        },
        {
            "dateparution": "2018-10-18",
            "id": "4436T3",
            "jugement": '{"famille": "Jugement d\'ouverture", "nature": "Jugement d\'ouverture de liquidation judiciaire", "date": "2018-10-05", "complementJugement": "Jugement d\'ouverture des opérations de la liquidation judiciaire", "type": "initial"}',
            "registre": ["422 734 970", "422734970"],
        },
    ],
}

MOCK_FAULTY_MERGED_DATA = {
    "total_count": 2,
    "results": [
        {
            "dateparution": "2018-10-18",
            "id": "4436T3",
            "jugement": '{"famille": "Jugement d\'ouverture", "nature": "Jugement d\'ouverture de liquidation judiciaire", "date": "2018-10-05", "complementJugement": "Jugement d\'ouverture des opérations de la liquidation judiciaire", "type": "initial"}',
        },
        {
            "dateparution": "2018-10-18",
            "id": "4432T3",
            "jugement": '{"famille": "Jugement d\'ouverture", "nature": "Jugement d\'ouverture de liquidation judiciaire", "date": "2018-10-05", "complementJugement": "Jugement d\'ouverture des opérations de la liquidation judiciaire", "type": "initial"}',
            "registre": ["422 734 970", "422734970"],
        },
    ],
}

MOCK_UNPROCESSABLE_JUDGEMENT = {
    "total_count": 1,
    "results": [
        {
            "dateparution": "2018-10-18",
            "id": "4436T3",
            "jugement": '{"famille": "Jugement d\'ouverture", "nature": "Jugement d\'ouverture", "date": "2018-10-05", "complementJugement": "Jugement d\'ouverture des opérations de la démarche judiciaire", "type": "initial"}',
            "registre": ["422 734 970", "422734970"],
        },
    ],
}

MOCK_GOUV_DATA = {
    "total_count": 2,
    "results": [
        {
            "dateparution": "2019-07-21",
            "id": "4436T3",
            "jugement": '{"famille": "Jugement de clôture", "nature": "Jugement de clôture pour insuffisance d\'actif", "date": "6 june 2011", "complementJugement": "Jugement prononçant la liquidation judiciaire", "type": "initial"}',
            "registre": ["897 572 376", "897572376"],
        },
        {
            "dateparution": "2018-10-18",
            "id": "4436T3",
            "jugement": '{"famille": "Jugement d\'ouverture", "nature": "Jugement d\'ouverture de liquidation judiciaire", "date": "2018-10-05", "complementJugement": "Jugement d\'ouverture des opérations de la liquidation judiciaire", "type": "initial"}',
            "registre": ["422 734 970", "422734970"],
        },
    ],
}


@pytest.fixture
def make_client():
    def _make(
        identifiers=MOCK_IDENTIFIERS,
        filter_start_date=datetime.datetime.strptime("2017-01-02", "%Y-%m-%d"),
        **kwargs,
    ):
        return CompanyRiskClient(
            all_identifiers=identifiers, filter_start_date=filter_start_date, **kwargs
        )

    return _make


def test_get_processed_risky_companies(make_client, mocker):
    client = make_client()
    mocker.patch.object(client, "get_risky_companies", return_value=MOCK_MERGED_DATA)

    result = client.get_processed_risky_companies()

    assert len(result) == 2
    sirens = [siren for siren in result.keys()]
    assert "897572376" in sirens
    assert 45 in sirens
    assert "0832" not in sirens


def test_get_processed_error_risky_companies(make_client, mocker):
    client = make_client()
    mocker.patch.object(
        client, "get_risky_companies", return_value=MOCK_FAULTY_MERGED_DATA
    )

    result = client.get_processed_risky_companies()

    warning = client.warnings[0]
    assert (
        str(warning)
        == "Record id 4436T3 raised an error: Mandatory registre property is missing"
    )
    assert len(result) == 1
    sirens = [siren for siren in result.keys()]
    assert 45 in sirens
    procedure = result[45][0]
    assert JudgmentEnum.LIQUIDATION == procedure.get("judgment")


def test_canot_process_judgement(make_client, mocker):
    client = make_client()
    mocker.patch.object(
        client, "get_risky_companies", return_value=MOCK_UNPROCESSABLE_JUDGEMENT
    )

    client.get_processed_risky_companies()

    warning = client.warnings[0]
    assert (
        str(warning)
        == "Record id 4436T3 raised an error: Cannot process judgment of Jugement d'ouverture"
    )


def test_get_processed_risky_companies_without_custom_identifiers(make_client, mocker):
    client = make_client(MOCK_SIRENS_ONLY)
    mocker.patch.object(client, "get_risky_companies", return_value=MOCK_MERGED_DATA)

    result = client.get_processed_risky_companies()

    sirens = [p for p in result.keys()]
    assert all(s in MOCK_SIRENS_ONLY for s in sirens)


def test_get_processed_risky_companies_with_sirets(make_client, mocker):
    """Sans identifiers, retourne une list"""
    client = make_client(MOCK_SIRETS_AS_IDENTIFIERS)
    mocker.patch.object(client, "get_risky_companies", return_value=MOCK_GOUV_DATA)

    result = client.get_processed_risky_companies()

    ids = [p for p in result.keys()]
    assert "8975723760004" in ids


def test_batch_size_at_limit(make_client, mocker):
    client = make_client(batch_size=140)
    mocker.patch.object(client, "get_risky_companies", return_value=MOCK_GOUV_DATA)
    assert client.batch_size == 140
    assert client.params is not None


def test_batch_size_over_limit(make_client):
    with pytest.raises(Exception) as exc_info:
        make_client(batch_size=150)

    assert BATCH_SIZE_ERROR in str(exc_info.value)


def test_errors_keep_running_across_batch(make_client, mocker):
    """
    Test that warnings are accumulated across batches and
    execution stops only on the first HTTP errors.
    """

    client = make_client(batch_size=1)  # Small batch size to trigger multiple batches
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_FAULTY_MERGED_DATA

    mocker.patch(
        "datagouvapi.client.requests.get",
        side_effect=[
            mock_response,
            exceptions.ConnectionError("any error message"),
        ],
    )

    result = client.get_processed_risky_companies()

    assert len(client.warnings) == 1
    assert "registre" in client.warnings[0].message
    assert len(result) == 1
    assert len(client.errors) == 1
    assert "refine" in client.errors[0]["params"]
    assert "any error message" in client.errors[0]["message"]


def test_parse_date_fin_from_complement_with_months():

    date_parution = datetime.date(2024, 1, 15)

    result = parse_date_fin_from_complement(
        complement_jugement="période d'observation de 6 mois", date_parution=date_parution
    )
    assert result == datetime.date(2024, 7, 15)


def test_parse_date_fin_from_complement_with_weeks():

    date_parution = datetime.date(2024, 1, 15)

    result = parse_date_fin_from_complement(
        complement_jugement="période d'observation de 4 semaines", date_parution=date_parution
    )
    assert result == datetime.date(2024, 2, 12)


def test_parse_date_fin_from_complement_with_days():

    date_parution = datetime.date(2024, 1, 15)

    result = parse_date_fin_from_complement(
        complement_jugement="délai de 30 jours", date_parution=date_parution
    )
    assert result == datetime.date(2024, 2, 14)


def test_parse_date_fin_from_complement_empty_returns_default():

    date_parution = datetime.date(2024, 1, 15)
    expected = date_parution + datetime.timedelta(days=DELAY_RECOVERY * 30)

    result = parse_date_fin_from_complement(
        complement_jugement="", date_parution=date_parution
    )
    assert result == expected


def test_parse_date_fin_from_complement_no_duration_returns_default():
    date_parution = datetime.date(2024, 1, 15)
    expected = date_parution + datetime.timedelta(days=DELAY_RECOVERY * 30)

    result = parse_date_fin_from_complement(
        complement_jugement="jugement d'ouverture", date_parution=date_parution
    )
    assert result == expected


def test_parse_date_fin_from_complement_none_date_parution():

    result = parse_date_fin_from_complement(
        complement_jugement="période d'observation de 6 mois", date_parution=None
    )
    assert result is None


def test_parse_date_fin_from_complement_delai_as_text():
    date_parution = datetime.date(2024, 1, 15)

    result = parse_date_fin_from_complement(
        complement_jugement="période d'observation de deux mois", date_parution=date_parution
    )
    assert result == datetime.date(2024, 3, 15)


def test_parse_date_fin_from_complement_delai_as_text_bis():
    date_parution = datetime.date(2024, 1, 15)

    result = parse_date_fin_from_complement(
        complement_jugement="période d'observation d'un mois", date_parution=date_parution
    )
    assert result == datetime.date(2024, 2, 15)
