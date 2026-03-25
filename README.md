[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![pypi](https://img.shields.io/pypi/v/datagouv-api.svg)](https://pypi.org/project/datagouv-api/)


# data-gouv-api

## French Gouv Opendata API clients
    
### Companies at risk 

Bankrupt and recovery assessments are recorded in the BODACC ; Bulletin officiel des annonces civiles et commerciales.
Each company is identified by its SIREN. SIRET is not recognized by the BODACC API. 
A custom identifier can be used to map your own IDs to the entity SIREN ; The goal is to facilitate any ulterior data processing with your database. 

This API will look for entities under reorganization and liquidation court judgments only ; other jugements imply an extended analysis for each company.

  #### How to use
        ```
            from datagouvapi.services.company_risk.company_risk import CompanyRiskClient
            siren_registry = ['123456789'] # or {'123456789': 123}
            api = CompanyRiskClient(
              all_identifiers=siren_registry,
              locale_name=None,
              filter_start_date=None
              api_key=None,
            )
            risky_companies = api.get_processed_risky_companies()

        ```
----
### School Holidays 
    TBD
