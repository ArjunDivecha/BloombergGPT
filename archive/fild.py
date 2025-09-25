"""Bloomberg field lookup utility.

Gracefully handles missing Bloomberg SDK elements so it can run without
crashing when optional parameters are unsupported.
"""
from __future__ import annotations

import sys
from typing import Dict, Iterable, List

try:
    import blpapi
    from blpapi import Session, SessionOptions
    from blpapi.exception import NotFoundException
except ImportError:  # pragma: no cover - informs user at runtime
    print(
        "ERROR: blpapi module not installed. Install via Bloomberg's API portal "
        "before running this script."
    )
    sys.exit(1)

FIELD_INFO_SERVICE = "//blp/apiflds"


def create_session() -> Session:
    options = SessionOptions()
    options.setServerHost("localhost")
    options.setServerPort(8194)

    session = Session(options)
    if not session.start():
        raise RuntimeError("Failed to start Bloomberg session.")
    if not session.openService(FIELD_INFO_SERVICE):
        session.stop()
        raise RuntimeError("Failed to open field information service.")
    return session


def _element_as_string(element: blpapi.Element, name: str) -> str:
    return element.getElementAsString(name) if element.hasElement(name) else ""


def _set_if_supported(request: blpapi.Request, name: str, value) -> None:
    if value is None:
        return
    try:
        request.set(name, value)
    except NotFoundException:
        print(f"Warning: '{name}' not supported by this environment; ignoring.")


def send_field_search_request(
    session: Session,
    search_text: str,
    *,
    exclude_field_type: str | None = "Static",
    max_results: int | None = 50,
) -> List[Dict[str, str]]:
    service = session.getService(FIELD_INFO_SERVICE)
    request = service.createRequest("FieldSearchRequest")
    request.set("searchSpec", search_text)
    _set_if_supported(request, "excludeFieldType", exclude_field_type)
    _set_if_supported(request, "returnFieldDocumentation", True)
    _set_if_supported(request, "maxResults", max_results)

    print(f"\nSubmitting FieldSearchRequest for: '{search_text}'\n")
    session.sendRequest(request)

    fields: List[Dict[str, str]] = []
    while True:
        event = session.nextEvent(500)
        for message in event:
            if message.hasElement("fieldData"):
                for field in message.getElement("fieldData").values():
                    fields.append(
                        {
                            "mnemonic": _element_as_string(field, "mnemonic"),
                            "description": _element_as_string(field, "description"),
                            "datatype": _element_as_string(field, "datatype"),
                            "category": _element_as_string(field, "categoryName"),
                            "id": _element_as_string(field, "id"),
                        }
                    )
        if event.eventType() == blpapi.Event.RESPONSE:
            break
    return fields


def send_field_info_request(session: Session, field_mnemonics: Iterable[str]) -> List[Dict[str, str]]:
    field_mnemonics = list(field_mnemonics)
    if not field_mnemonics:
        return []

    service = session.getService(FIELD_INFO_SERVICE)
    request = service.createRequest("FieldInfoRequest")
    for mnemonic in field_mnemonics:
        request.append("id", mnemonic)

    print(f"\nSubmitting FieldInfoRequest for fields: {field_mnemonics}\n")
    session.sendRequest(request)

    metadata: List[Dict[str, str]] = []
    while True:
        event = session.nextEvent(500)
        for message in event:
            if message.hasElement("fieldData"):
                for field in message.getElement("fieldData").values():
                    metadata.append(
                        {
                            "mnemonic": _element_as_string(field, "mnemonic"),
                            "description": _element_as_string(field, "description"),
                            "datatype": _element_as_string(field, "datatype"),
                            "field_type": _element_as_string(field, "fieldType"),
                            "documentation": _element_as_string(field, "documentation"),
                            "group": _element_as_string(field, "categoryName"),
                            "id": _element_as_string(field, "id"),
                        }
                    )
        if event.eventType() == blpapi.Event.RESPONSE:
            break
    return metadata


def main() -> None:
    session = create_session()
    try:
        search_keyword = "India CPI"
        field_results = send_field_search_request(session, search_keyword)

        print(f"\n{len(field_results)} fields found for '{search_keyword}':")
        for field in field_results:
            print(
                f" - {field['mnemonic']} ({field['description']}) "
                f"[{field['datatype']}]"
            )

        top_mnemonics = [field["mnemonic"] for field in field_results[:5] if field.get("mnemonic")]
        if not top_mnemonics:
            print("No fields returned from search; skipping FieldInfoRequest.")
            return

        field_metadata = send_field_info_request(session, top_mnemonics)

        print("\nDetailed Field Metadata:")
        for meta in field_metadata:
            print(f"\nField: {meta['mnemonic']}")
            print(f"Description: {meta['description']}")
            print(f"Type: {meta['field_type']}")
            print(f"Group: {meta['group']}")
            print(f"Data Type: {meta['datatype']}")
            snippet = (meta["documentation"] or "")[:200]
            print(f"Documentation: {snippet}...\n")
    finally:
        session.stop()


if __name__ == "__main__":
    main()
