import pytest

from datagouvapi.services.company_risk.company_risk import CompanyRiskClient
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
            "jugement": '{"famille": "Jugement de clôture", "nature": "Jugement de clôture pour insuffisance d\'actif", "date": "6 mai 2011", "complementJugement": "Jugement prononçant la liquidation judiciaire", "type": "initial"}',
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

MOCK_INCOMPLETE_MERGED_DATA_J = {
    "total_count": 1,
    "results": [
        {
            "dateparution": "2018-10-18",
            "id": "4436T3",
            "jugement": '{"famille": "Jugement d\'ouverture", "nature": "Jugement d\'ouverture de liquidation judiciaire", "date": "2018-10-05", "complementJugement": "Jugement d\'ouverture des opérations de la liquidation judiciaire", "type": "initial"}',
        },
    ],
}

MOCK_GOUV_DATA = {
    "total_count": 2,
    "results": [
        {
            "dateparution": "2019-07-21",
            "id": "4436T3",
            "jugement": '{"famille": "Jugement de clôture", "nature": "Jugement de clôture pour insuffisance d\'actif", "date": "6 mai 2011", "complementJugement": "Jugement prononçant la liquidation judiciaire", "type": "initial"}',
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
    def _make(identifiers=MOCK_IDENTIFIERS, filter_start_date="2017-01-02", **kwargs):
        return CompanyRiskClient(
            all_identifiers=identifiers,
            filter_start_date=filter_start_date,
            **kwargs
        )
    return _make


def test_get_processed_risky_companies(make_client, mocker):
    client = make_client()
    mocker.patch.object(
        client, "get_risky_companies", return_value=MOCK_MERGED_DATA
    )

    result = client.get_processed_risky_companies()

    assert len(result) == 2
    sirens = [siren for siren in result.keys()]
    assert "897572376" in sirens
    assert 45 in sirens


def test_get_processed_error_risky_companies(make_client, mocker):
    client = make_client()
    mocker.patch.object(
        client, "get_risky_companies", return_value=MOCK_FAULTY_MERGED_DATA
    )

    result = client.get_processed_risky_companies()

    warning = client.warnings[0]
    assert str(warning) == 'Record id 4436T3 raised an error: Mandatory registre property is missing'
    assert len(result) == 1
    sirens = [siren for siren in result.keys()]
    assert 45 in sirens
    assert result[45][0]['judgment'] == JudgmentEnum.LIQUIDATION

def test_get_processed_risky_companies_procedure(make_client, mocker):
    client = make_client()
    mocker.patch.object(
        client, "get_risky_companies", return_value=MOCK_MERGED_DATA
    )

    result = client.get_processed_risky_companies()

    procedures = [p["judgment"] for records in result.values() for p in records]
    assert JudgmentEnum.LIQUIDATION in procedures


def test_get_processed_risky_companies_faulty_siren_ignored(make_client, mocker):
    """'0832' is in the given identifiers but not in any registry of the results — it will be ignored in the process"""
    client = make_client()
    mocker.patch.object(
        client, "get_risky_companies", return_value=MOCK_GOUV_DATA["results"]
    )

    result = client.get_processed_risky_companies()

    sirets = [p for p in result.keys()]
    assert "0832" not in sirets


def test_get_processed_risky_companies_without_custom_identifiers(make_client, mocker):
    client = make_client(identifiers=MOCK_SIRENS_ONLY)
    mocker.patch.object(
        client, "get_risky_companies", return_value=MOCK_GOUV_DATA["results"]
    )

    result = client.get_processed_risky_companies()

    sirens = [p for p in result.keys()]
    assert "422734970" in sirens


def test_get_processed_risky_companies_with_sirets(make_client, mocker):
    """Sans identifiers, retourne une liste"""
    client = make_client(MOCK_SIRETS_AS_IDENTIFIERS)
    mocker.patch.object(
        client, "get_risky_companies", return_value=MOCK_GOUV_DATA["results"]
    )

    result = client.get_processed_risky_companies()

    ids = [p for p in result.keys()]
    assert "8975723760004" in ids

def test_batch_size_at_limit(make_client):
    client = make_client(batch_size=140)

    assert client.batch_size == 140


def test_batch_size_over_limit(make_client):
    with pytest.raises(
        CompanyRiskClient,
        match="'GOUV API error on test : Batch size cannot be more than 140 ; HTTP request will be rejected'",
    ):
        make_client(batch_size=150),


def test_errors_accumulate_across_batch(make_client):
    client = make_client()

    batch_params = [
        {f"registre in ('12345678{i}', '12345678{i + 2}')"} for i in range(5)
    ]
    for params in batch_params:
        client.get_data(params=params)

    assert len(client.errors) == 5
    assert {
        "message": "Timeout error",
        "params": {"registre in ('123456783', '123456785')"},
        "status_code": None,
    } in client.errors

#
# def test_errors_keep_running_across_batch(mock_get, client):
#
#     mock_get.side_effect = [
#         MagicMock(
#             **{
#                 "raise_for_status.return_value": None,
#                 "json.return_value": _make_result(),
#             }
#         ),
#         requests.exceptions.Timeout(),
#         requests.exceptions.Timeout(),
#     ]
#
#     batch_params = [
#         {f"registre in ('12345678{i}', '12345678{i + 2}')"} for i in range(3)
#     ]
#     [client.get_data(params=params) for params in batch_params]
#
#     results = []
#     for params in batch_params:
#         with pytest.raises(requests.exceptions.Timeout):
#             results.append(client.get_data(params=params))

#
# def test_success_returns_json(mock_get, client):
#     mock_get.return_value.json.return_value = _make_result()
#     mock_get.return_value.raise_for_status.return_value = None
#
#     client.get_data(params=_make_where_clause())
#
#     assert len(client.errors) == 0
