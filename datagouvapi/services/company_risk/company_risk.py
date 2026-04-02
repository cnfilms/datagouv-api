import json
import logging
import re
from datetime import date, datetime
from typing import Optional, Union

import requests
from dateutil.relativedelta import relativedelta
from text_to_num import alpha2digit  # type: ignore[import]

from datagouvapi.client import GouvApiClient
from datagouvapi.services.company_risk.constants import (
    BASE_WHERE_CLAUSE,
    DATE_FORMATS,
    API_URL,
    DELAY_RECOVERY,
    API_SEARCH_PARAMS,
    MAX_BATCH_SIZE,
    BATCH_SIZE_ERROR,
    MANDATORY_FIELDS,
)
from datagouvapi.services.company_risk.models import (
    JudgmentEnum,
    CompanyJudgment,
    Identifier,
    Siren,
    SirenIndex,
)
from datagouvapi.tools.helpers import unaccent, merge_gouv_data

logger = logging.getLogger(__name__)

from datagouvapi.tools.models import GouvSearchResult


class CompanyRiskClient(GouvApiClient):
    """
        BODACC-specific api client to interrogate a list of companies and see their publications.
    param: all_identifiers: list of SIREN strings, or dict mapping SIREN to your own identifiers (string, integer or UUID).
    param: api_key: Optional, api key for the BODACC API
    param: filter_start_date: Optional, to restrict the search - Format 'YYYY-MM-DD'
    param: filter_end_date: Optional, to restrict the search - Format 'YYYY-MM-DD'
    param: batch_size: Default is 140, limit for number of SIREN in one batch, to avoid http params overload.
    """

    def __init__(
        self,
        all_identifiers: Union[list[Siren], SirenIndex],
        filter_start_date=None,
        filter_end_date=None,
        batch_size=MAX_BATCH_SIZE,
        **kwargs,
    ):
        super().__init__(api_url=API_URL, **kwargs)
        self.batch_size = batch_size
        if self.batch_size > MAX_BATCH_SIZE:
            self._raise(BATCH_SIZE_ERROR)
        self.identifiers = all_identifiers
        self.siren_list = (
            list(self.identifiers.keys())
            if isinstance(self.identifiers, dict)  # implicitely SirenIndex
            else self.identifiers
        )
        self.filter_start_date = filter_start_date
        self.filter_end_date = filter_end_date
        self.params = API_SEARCH_PARAMS

    def _compute_where_clause(self, batch_siren_list: list[Siren]) -> str:

        sirens_quoted = ", ".join([f'"{s}"' for s in batch_siren_list])
        clause = f"registre IN ({sirens_quoted}) and {BASE_WHERE_CLAUSE}"
        if self.filter_start_date:
            clause += (
                f"and dateparution >= '{self.filter_start_date.strftime('%Y-%m-%d')}'"
            )
        if self.filter_end_date:
            clause += (
                f"and dateparution <= '{self.filter_end_date.strftime('%Y-%m-%d')}'"
            )
        return clause

    def _build_company_judgment(
        self, item: dict[str, str], siren: Siren, identifier: Optional[Identifier]
    ) -> Optional[CompanyJudgment]:
        """
            Resolve the response from BODACC-api into a CompanyJudgment dict.
        :param item: publication object
        :param siren: SIREN of the company
        :param identifier: Optional, custom identifier for the company.
        """
        record_id = item["id"]
        if not (raw_jugement := json.loads(item["jugement"])):
            return None
        raw_complement = raw_jugement.get("complementJugement")
        raw_nature = raw_jugement.get("nature")
        raw_date = raw_jugement.get("date")

        if not (raw_complement or raw_nature or raw_date):
            return None

        if not (
            current_judgment := self.resolve_judgment(raw_nature)
            or self.resolve_judgment(raw_complement)
        ):
            self._add_warning(record_id, f"Cannot process judgment of {raw_nature}")
            return None

        if not (record_date := self.resolve_date(item["dateparution"])):
            self._add_warning(record_id, f"Cannot process date: {item['dateparution']}")
            return None

        date_fin = (
            parse_date_fin_from_complement(
                date_parution=record_date, complement_jugement=raw_complement
            )
            if current_judgment == JudgmentEnum.REDRESSEMENT
            else None
        )

        return CompanyJudgment(
            siren=siren,
            identifier=identifier,
            record_id=record_id,
            date=record_date,
            raw_data=raw_jugement,
            judgment=current_judgment,
            expected_end_date=date_fin,
        )

    def get_processed_risky_companies(self) -> dict[Identifier, list[CompanyJudgment]]:
        """
            Map a risk judgment for each company.
        :return: A registry mapping the SIREN or custom ID to its list of recovery and bankrupt court judgments.
        """
        parsed_douteux: dict[Identifier, list[CompanyJudgment]] = dict()

        for item in self.get_risky_companies().get("results", []):
            if missing_field := next(
                (field for field in MANDATORY_FIELDS if not item.get(field)), None
            ):
                self._add_warning(
                    item["id"], f"Mandatory {missing_field} property is missing"
                )
                continue

            if not (
                siren := next(
                    (s for s in self.siren_list if s in item["registre"]), None
                )
            ):
                continue
            identifier = (
                self.identifiers.get(siren, siren)
                if isinstance(self.identifiers, dict)
                else siren
            )

            if not (
                judgement_obj := self._build_company_judgment(item, siren, identifier)
            ):
                self._add_warning(item["id"], "Judgement cannot be processed")
                continue

            if identifier not in parsed_douteux:
                parsed_douteux[identifier] = []

            parsed_douteux[identifier].append(judgement_obj)

        return parsed_douteux

    def resolve_date(self, date_str: str) -> Optional[date]:
        """
        Format date string into a usable datetime.date object.
        """
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        return None

    @classmethod
    def resolve_judgment(cls, jugement: str) -> Optional[JudgmentEnum]:
        jugement = unaccent(jugement).lower()
        if "créances" in jugement:
            return None
        if any(word in jugement for word in ("annulation", "infirmation")):
            return JudgmentEnum.ANNULEE

        if any(word in jugement for word in ("liquidation", "cession")):
            return JudgmentEnum.LIQUIDATION

        if "resolution" in jugement and any(
            w in jugement for w in ("redressement", "continuation")
        ):
            return JudgmentEnum.LIQUIDATION

        if any(word in jugement for word in ("redressement", "continuation")):
            return JudgmentEnum.REDRESSEMENT

        return None

    def get_risky_companies(self) -> GouvSearchResult:
        """
            Interrogate the API until we searched all SIREN numbers, according to the given batch size.
            Merge data of each batch into one functional dict.
        :return: GouvSearchResult
        """
        _raw_data = []
        for i in range(0, 500, self.batch_size):
            batch_siren_list = self.siren_list[i : i + self.batch_size]
            self.params["where"] = self._compute_where_clause(
                batch_siren_list=batch_siren_list
            )
            try:
                batch_douteux = self.get_data(params=self.params)
            except requests.exceptions.RequestException as e:
                self._add_error(str(e), str(self.params))
                logging.error(str(e))
                break
            _raw_data.append(batch_douteux)
        return merge_gouv_data(_raw_data)


def parse_date_fin_from_complement(
    complement_jugement: str, date_parution: date
) -> Optional[date]:
    """
    Parse the complementJugement field to extract a custom duration for redressement.

    By default, redressement is 2 months, but the complement_jugement may specify
    a different duration (e.g., "période d'observation de 6 mois").

    :param complement_jugement: The complementJugement field from Bodacc raw data
    :param date_parution: The Boddac publication date
    :return: The calculated end date
    """

    if not complement_jugement:
        return (
            date_parution + relativedelta(months=DELAY_RECOVERY)
            if date_parution
            else None
        )

    complement_lower = complement_jugement.lower().replace("'", " ")
    # Pattern is usually: "6 mois", "six mois", etc.
    complement_numbers = alpha2digit(complement_lower, lang="fr", threshold=0)

    years_pattern = r"(\d+)\s*ans?"
    months_pattern = r"(\d+)\s*mois"
    weeks_pattern = r"(\d+)\s*semaines?"
    days_pattern = r"(\d+)\s*jours?"

    year_match = re.search(years_pattern, complement_numbers)
    if year_match:
        years = int(year_match.group(1))
        return date_parution + relativedelta(years=years) if date_parution else None

    months_match = re.search(months_pattern, complement_numbers)
    if months_match:
        months = int(months_match.group(1))
        return date_parution + relativedelta(months=months) if date_parution else None

    weeks_match = re.search(weeks_pattern, complement_numbers)
    if weeks_match:
        weeks = int(weeks_match.group(1))
        return date_parution + relativedelta(weeks=weeks) if date_parution else None

    days_match = re.search(days_pattern, complement_numbers)
    if days_match:
        days = int(days_match.group(1))
        return date_parution + relativedelta(days=days) if date_parution else None

    # Default to 2 months
    return (
        date_parution + relativedelta(months=DELAY_RECOVERY) if date_parution else None
    )
