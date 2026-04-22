from typing import Any, List, Mapping, Tuple

from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
import requests

from .streams import (
    Addresses,
    Companies,
    Contacts,
    Leads,
    ProductItems,
    SalesInvoiceHeaders,
    SalesLedgers,
    SalesOrderHeaders,
    SalesTransactions,
)


class SourceProspectCrm(AbstractSource):
    def check_connection(self, logger, config: Mapping[str, Any]) -> Tuple[bool, Any]:
        try:
            resp = requests.get(
                "https://crm-odata-v1.prospect365.com/Contacts?$top=1",
                headers={"Authorization": f"Bearer {config['api_key']}"},
                timeout=10,
            )
            resp.raise_for_status()
            return True, None
        except Exception as e:
            return False, str(e)

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        api_key = config["api_key"]
        return [
            Contacts(api_key=api_key),
            Companies(api_key=api_key),
            SalesLedgers(api_key=api_key),
            Leads(api_key=api_key),
            SalesTransactions(api_key=api_key),
            ProductItems(api_key=api_key),
            Addresses(api_key=api_key),
            SalesOrderHeaders(api_key=api_key),
            SalesInvoiceHeaders(api_key=api_key),
        ]
