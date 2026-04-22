from abc import ABC, abstractmethod
from typing import Any, Iterable, Mapping, MutableMapping, Optional
import urllib.parse

import requests
from airbyte_cdk.sources.streams.http import HttpStream


class ProspectCrmStream(HttpStream, ABC):
    url_base = "https://crm-odata-v1.prospect365.com/"
    page_size = 500

    def __init__(self, api_key: str, **kwargs):
        super().__init__(**kwargs)
        self._api_key = api_key

    def request_headers(self, **kwargs) -> Mapping[str, Any]:
        return {"Authorization": f"Bearer {self._api_key}"}

    @property
    @abstractmethod
    def entity_name(self) -> str:
        pass

    def path(self, **kwargs) -> str:
        return self.entity_name

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        records = response.json().get("value", [])
        if len(records) < self.page_size:
            return None
        parsed = urllib.parse.urlparse(response.request.url)
        params = urllib.parse.parse_qs(parsed.query)
        current_skip = int(params.get("%24skip", params.get("$skip", ["0"]))[0])
        return {"skip": current_skip + self.page_size}

    def request_params(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> MutableMapping[str, Any]:
        params: MutableMapping[str, Any] = {"$top": self.page_size}
        if next_page_token:
            params["$skip"] = next_page_token["skip"]
        return params

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        yield from response.json().get("value", [])


class IncrementalProspectCrmStream(ProspectCrmStream):
    cursor_field = "LastUpdatedTimestamp"

    @property
    def state_checkpoint_interval(self) -> int:
        return self.page_size

    def get_updated_state(
        self,
        current_stream_state: MutableMapping[str, Any],
        latest_record: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        record_cursor = latest_record.get(self.cursor_field) or ""
        state_cursor = current_stream_state.get(self.cursor_field) or ""
        return {self.cursor_field: max(record_cursor, state_cursor)}

    def request_params(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> MutableMapping[str, Any]:
        params: MutableMapping[str, Any] = {
            "$top": self.page_size,
            "$orderby": f"{self.cursor_field} asc",
        }
        cursor_value = (stream_state or {}).get(self.cursor_field)
        if cursor_value:
            params["$filter"] = f"{self.cursor_field} gt {cursor_value}"
        if next_page_token:
            params["$skip"] = next_page_token["skip"]
        return params


# ── Incremental streams ────────────────────────────────────────────────────────

class Contacts(IncrementalProspectCrmStream):
    primary_key = "ContactId"
    entity_name = "Contacts"


class Companies(IncrementalProspectCrmStream):
    primary_key = "CompanyId"
    entity_name = "Companies"


class SalesLedgers(IncrementalProspectCrmStream):
    primary_key = "SalesLedgerId"
    entity_name = "SalesLedgers"


class Leads(IncrementalProspectCrmStream):
    primary_key = "LeadId"
    entity_name = "Leads"


class SalesTransactions(IncrementalProspectCrmStream):
    primary_key = "Id"
    entity_name = "SalesTransactions"


class ProductItems(IncrementalProspectCrmStream):
    primary_key = "ProductItemId"
    entity_name = "ProductItems"


class Addresses(IncrementalProspectCrmStream):
    primary_key = "AddressId"
    entity_name = "Addresses"


# ── Full-refresh streams (no LastUpdatedTimestamp) ─────────────────────────────

class SalesOrderHeaders(ProspectCrmStream):
    primary_key = "OrderNumber"
    entity_name = "SalesOrderHeaders"


class SalesInvoiceHeaders(ProspectCrmStream):
    primary_key = "InvoiceNumber"
    entity_name = "SalesInvoiceHeaders"
