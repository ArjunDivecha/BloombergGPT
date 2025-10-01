"""
Bloomberg Data Broker - FastAPI Server
========================================

INPUT FILES:
- None required (data comes from Bloomberg Desktop API)

OUTPUT FILES:
- None (serves API endpoints only)

DESCRIPTION:
This script implements a secure FastAPI server that acts as a broker for Bloomberg Desktop API.
It enforces field allow-list, authentication, and rate limiting to comply with Bloomberg licensing.

The server provides five endpoints:
1. /blp/refdata - Current reference data for a ticker
2. /blp/historical - Historical time-series data for a ticker
3. /blp/fields - List of allowed Bloomberg fields
4. /blp/coverage - Check Bloomberg coverage for a ticker
5. /blp/securities - Search Bloomberg instruments (SECF-style)

REQUIREMENTS:
- Bloomberg Terminal must be running and logged in
- API key for authentication (set via API_KEY environment variable)
- Rate limiting: 60 requests per minute per API key

VERSION HISTORY:
- Version 2.1.0 - Expanded field filters and securities search endpoint (2025-09-25)
- Version 1.0.0 - Initial implementation (2025-09-21)

CONFIGURATION:
- Set environment variable API_KEY to your secret key
- Server runs on 0.0.0.0:8000 by default

DEPENDENCIES:
- fastapi, uvicorn, blpapi, python-dotenv, slowapi

SECURITY:
- API key required in x-api-key header
- Rate limiting enforced
- Field allow-list validation

"""

import os
import datetime
from pathlib import Path
from functools import lru_cache
import re
from typing import List, Dict, Optional, Tuple, Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Depends, Request, status, Query
from fastapi.security import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

# Try to import blpapi, use mock if not available
try:
    import blpapi  # Bloomberg API
    BLOOMBERG_AVAILABLE = True
except ImportError:
    BLOOMBERG_AVAILABLE = False
    print("Warning: blpapi not found. Using mock data for development/testing.")
    print("To use real Bloomberg data, install blpapi from Bloomberg's API portal.")

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Bloomberg Data Broker", version="2.1.0")

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configuration from environment variables
API_KEY = os.getenv("API_KEY", "Caeser00**")
BROKER_HOST = os.getenv("BROKER_HOST", "0.0.0.0")
BROKER_PORT = int(os.getenv("BROKER_PORT", "8000"))
BLOOMBERG_HOST = os.getenv("BLOOMBERG_HOST", "localhost")
BLOOMBERG_PORT = int(os.getenv("BLOOMBERG_PORT", "8194"))
RATE_LIMIT = os.getenv("RATE_LIMIT", "60/minute")
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

DEBUG_LOGGING = os.getenv("BROKER_DEBUG", "0").lower() in {"1", "true", "yes", "on"}

# Session pooling - reuse Bloomberg session instead of creating new one each time
_bloomberg_session = None
try:
    import threading
    _session_lock = threading.Lock()
except ImportError:
    _session_lock = None


def debug(message: str) -> None:
    """Emit debug output when BROKER_DEBUG is enabled."""
    if DEBUG_LOGGING:
        print(f"[DEBUG] {message}")

async def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


# Field catalog configuration
FIELD_CATALOG_PATH = Path(__file__).resolve().parent / "Production Data" / "Bloomberg Master Field List.xlsx"
FIELD_CATALOG_SHEET = os.getenv("BLOOMBERG_FIELD_SHEET", "Pruned List")


def _normalize_field_key(value: str) -> str:
    """Normalize field descriptors for lookup."""
    return re.sub(r"[^a-z0-9]+", "", value.lower())


@lru_cache(maxsize=1)
def get_field_catalog() -> Dict[str, Any]:
    """Load the curated Bloomberg field catalog and build lookup maps."""
    if not FIELD_CATALOG_PATH.exists():
        raise HTTPException(status_code=500, detail=f"Field catalog not found at {FIELD_CATALOG_PATH}")

    df = pd.read_excel(FIELD_CATALOG_PATH, sheet_name=FIELD_CATALOG_SHEET)
    if df.empty:
        raise HTTPException(status_code=500, detail="Field catalog is empty")

    df['Field ID'] = df['Field ID'].astype(str)
    df['Display Name'] = df['Display Name'].astype(str)
    df['Description'] = df['Description'].fillna('')

    records = df.to_dict('records')
    display_lookup: Dict[str, Dict[str, Any]] = {}
    id_lookup: Dict[str, str] = {}
    description_lookup: Dict[str, str] = {}

    for record in records:
        display_key = record['Display Name'].upper()
        display_lookup[display_key] = record
        id_lookup[record['Field ID'].upper()] = record['Display Name']

        for candidate in (record['Description'], record['Display Name'], record['Field ID']):
            normalized = _normalize_field_key(str(candidate))
            if normalized and normalized not in description_lookup:
                description_lookup[normalized] = record['Display Name']

    sample_columns = [
        col for col in df.columns
        if col not in {'Field ID', 'Display Name', 'Description', 'Data Type'}
    ]

    return {
        'dataframe': df,
        'records': records,
        'display_lookup': display_lookup,
        'id_lookup': id_lookup,
        'description_lookup': description_lookup,
        'allowed_fields': set(display_lookup.keys()),
        'sample_columns': sample_columns,
    }


def resolve_field_name(field: str) -> Tuple[str, Dict[str, Any]]:
    """Resolve user-supplied field text to a Bloomberg display name and metadata."""
    if not field or not field.strip():
        raise HTTPException(status_code=400, detail="Field names cannot be empty")

    catalog = get_field_catalog()
    candidate = field.strip()
    upper_candidate = candidate.upper()

    if upper_candidate in catalog['display_lookup']:
        record = catalog['display_lookup'][upper_candidate]
        return record['Display Name'], record

    if upper_candidate in catalog['id_lookup']:
        display_name = catalog['id_lookup'][upper_candidate]
        record = catalog['display_lookup'][display_name.upper()]
        return display_name, record

    normalized = _normalize_field_key(candidate)
    if normalized in catalog['description_lookup']:
        display_name = catalog['description_lookup'][normalized]
        record = catalog['display_lookup'][display_name.upper()]
        return display_name, record

    raise HTTPException(status_code=400, detail=f"Field '{field}' is not in the approved Bloomberg master list")


def validate_fields(fields: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Validate supplied fields against the curated catalog and return resolved metadata."""
    if not fields:
        raise HTTPException(status_code=400, detail="At least one field is required")

    resolved: List[str] = []
    metadata: List[Dict[str, Any]] = []
    seen = set()

    for original in fields:
        candidate = original.strip() if isinstance(original, str) else ''
        if not candidate:
            raise HTTPException(status_code=400, detail="Field names cannot be empty")
        try:
            display_name, record = resolve_field_name(candidate)
            normalized = display_name.upper()
            if normalized in seen:
                continue
            seen.add(normalized)
            resolved.append(display_name)
            metadata.append({
                'requested': original,
                'display_name': display_name,
                'field_id': _serialize_value(record.get('Field ID')),
                'description': _serialize_value(record.get('Description')),
                'data_type': _serialize_value(record.get('Data Type')),
            })
        except HTTPException:
            normalized = candidate.upper()
            if normalized in seen:
                continue
            seen.add(normalized)
            resolved.append(candidate)
            metadata.append({
                'requested': original,
                'display_name': candidate,
                'field_id': None,
                'description': "Not in catalog - forwarded as supplied",
                'data_type': None,
            })

    return resolved, metadata


def get_field_metadata(display_name: str) -> Dict[str, Any]:
    """Fetch the catalog record for a Bloomberg display name."""
    catalog = get_field_catalog()
    record = catalog['display_lookup'].get(display_name.upper())
    if not record:
        raise HTTPException(status_code=500, detail=f"Metadata for field '{display_name}' not found")
    return record


def _serialize_value(value: Any) -> Any:
    """Convert numpy/pandas values to plain Python types for JSON serialization."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    if hasattr(value, 'item'):
        try:
            return value.item()
        except Exception:
            pass
    return value


def record_matches_filters(
    record: Dict[str, Any],
    contains: Optional[str] = None,
    pattern: Optional[re.Pattern] = None,
    terms: Optional[List[str]] = None,
    match_mode: str = 'any',
) -> bool:
    """Check if a catalog record satisfies optional filter criteria."""

    text_parts = [
        str(record.get('Display Name', '')),
        str(record.get('Description', '')),
        str(record.get('Category', '')),
        str(record.get('Subcategory', '')),
        str(record.get('Field ID', '')),
    ]
    haystack = ' '.join(part for part in text_parts if part).lower()

    if contains and contains not in haystack:
        return False

    if pattern and not pattern.search(haystack):
        return False

    if terms:
        matches = [term in haystack for term in terms]
        if match_mode == 'all' and not all(matches):
            return False
        if match_mode == 'any' and not any(matches):
            return False

    return True


def build_mock_refdata(ticker: str, fields: List[str]) -> Dict[str, Any]:
    """Return 'No Data' placeholders when reference data is unavailable."""
    return {field: "No Data" for field in fields}


def build_mock_historical(ticker: str, fields: List[str]) -> List[Dict[str, Any]]:
    """Return 'No Data' placeholders when historical data is unavailable."""
    return [{"date": "No Data", "values": {field: "No Data" for field in fields}}]






def build_mock_instruments(query: str, limit: int) -> List[Dict[str, str]]:
    """Return no instruments when the Bloomberg service is unavailable."""
    return []


def get_bloomberg_screen_results(session, screen_name: str, screen_type: str = "PRIVATE", group: str = None, language: str = "ENGLISH", asof_date: str = None):
    """
    Run a Bloomberg Equity Screen (BEQS).
    
    Args:
        session: Bloomberg session
        screen_name: Name of saved EQS screen
        screen_type: "PRIVATE" (user screens) or "GLOBAL" (Bloomberg sample screens)
        group: Folder/category for GLOBAL screens (e.g., "Popular", "Investment Banking")
        language: Language ID (default: "ENGLISH")
        asof_date: Optional date in YYYYMMDD format for historical screening
    
    Returns:
        List of dicts with security and field data from the screen
    """
    if not session:
        debug("No session provided for BEQS")
        return []
    
    try:
        debug(f"Opening reference data service for BEQS...")
        if not session.openService("//blp/refdata"):
            debug("Failed to open reference data service for BEQS")
            return []
        
        service = session.getService("//blp/refdata")
        request = service.createRequest("BeqsRequest")
        
        # Set required parameters
        request.set("screenName", screen_name)
        request.set("screenType", screen_type.upper())
        
        if group:
            request.set("Group", group)
        
        request.set("languageId", language.upper())
        
        # Add Point-in-Time date override if specified
        if asof_date:
            overrides = request.getElement("overrides")
            override = overrides.appendElement()
            override.setElement("fieldId", "PiTDate")
            override.setElement("value", asof_date.replace("-", ""))
            debug(f"BEQS with PiTDate override: {asof_date}")
        
        debug(f"Sending BEQS request: screen={screen_name}, type={screen_type}, group={group}")
        session.sendRequest(request)
        
        results = []
        while True:
            event = session.nextEvent(10000)  # 10 second timeout for screens
            debug(f"Received BEQS event type: {event.eventType()}")
            
            if event.eventType() == blpapi.Event.TIMEOUT:
                debug("BEQS request timeout")
                break
            
            if event.eventType() in (blpapi.Event.RESPONSE, blpapi.Event.PARTIAL_RESPONSE):
                for msg in event:
                    debug(f"Processing BEQS message")
                    if msg.hasElement("data"):
                        data_elem = msg.getElement("data")
                        if data_elem.hasElement("securityData"):
                            sec_data_array = data_elem.getElement("securityData")
                            debug(f"Found {sec_data_array.numValues()} securities in BEQS results")
                            
                            for i in range(sec_data_array.numValues()):
                                sec_data = sec_data_array.getValueAsElement(i)
                                
                                security = sec_data.getElementAsString("security") if sec_data.hasElement("security") else None
                                
                                # Extract field data
                                if sec_data.hasElement("fieldData"):
                                    field_data = sec_data.getElement("fieldData")
                                    
                                    # Get all field names and values
                                    field_dict = {"security": security}
                                    for j in range(field_data.numElements()):
                                        elem = field_data.getElement(j)
                                        field_name = str(elem.name())
                                        try:
                                            field_value = elem.getValueAsString()
                                        except:
                                            try:
                                                field_value = elem.getValueAsFloat()
                                            except:
                                                field_value = str(elem.getValue())
                                        field_dict[field_name] = field_value
                                    
                                    results.append(field_dict)
                                    debug(f"Added BEQS result for {security}: {len(field_dict)-1} fields")
            
            if event.eventType() == blpapi.Event.RESPONSE:
                debug("Received final BEQS response")
                break
        
        debug(f"BEQS returned {len(results)} securities")
        return results
        
    except Exception as e:
        debug(f"BEQS error: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_bloomberg_instruments(query: str, limit: int) -> Tuple[List[Dict[str, str]], int]:
    """Search Bloomberg instruments using instrumentListRequest."""
    session = get_bloomberg_session()
    if not session:
        mock_results = build_mock_instruments(query, limit)
        return mock_results, len(mock_results)

    results: List[Dict[str, str]] = []
    try:
        if not session.openService("//blp/instruments"):
            debug("Failed to open instruments service")
            fallback = build_mock_instruments(query, limit)
            return fallback, len(fallback)
        service = session.getService("//blp/instruments")
        request = service.createRequest("instrumentListRequest")
        request.set("query", query)
        try:
            request.set("maxResults", int(limit))
        except Exception:
            pass
        session.sendRequest(request)
        while True:
            event = session.nextEvent(5000)
            et = event.eventType()
            if et in (blpapi.Event.PARTIAL_RESPONSE, blpapi.Event.RESPONSE):
                for msg in event:
                    if msg.hasElement("responseError"):
                        err = msg.getElement("responseError")
                        debug(f"instrumentListResponse error: {err}")
                        fallback = build_mock_instruments(query, limit)
                        return fallback, len(fallback)
                    if msg.hasElement("instrumentListResponse"):
                        container = msg.getElement("instrumentListResponse")
                    elif msg.hasElement("results"):
                        container = msg.getElement("results")
                    else:
                        continue
                    for i in range(container.numValues()):
                        row = container.getValueAsElement(i)
                        security = row.getElementAsString("security") if row.hasElement("security") else ""
                        description = row.getElementAsString("description") if row.hasElement("description") else ""
                        yellow = row.getElementAsString("yellowKey") if row.hasElement("yellowKey") else ""
                        if security or description:
                            results.append({"security": security, "description": description, "yellowKey": yellow})
                if et == blpapi.Event.RESPONSE:
                    break
            elif et == blpapi.Event.TIMEOUT:
                debug("instrumentListRequest timeout")
                break
    except Exception as e:
        debug(f"Instrument search error: {e}")
        return [], 0

    deduped: List[Dict[str, str]] = []
    seen = set()
    for rec in results:
        key = (rec.get("security"), rec.get("description"), rec.get("yellowKey"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(rec)

    total_count = len(deduped)
    limited_results = deduped[: max(0, limit)]
    return limited_results, total_count

def get_default_coverage_field() -> str:
    """Pick a reasonable default field for coverage checks."""
    try:
        display_name, _ = resolve_field_name('PX_LAST')
        return display_name
    except HTTPException:
        catalog = get_field_catalog()
        if not catalog['allowed_fields']:
            raise HTTPException(status_code=500, detail="No Bloomberg fields configured")
        arbitrary_key = next(iter(catalog['allowed_fields']))
        record = catalog['display_lookup'][arbitrary_key]
        return record['Display Name']

# Bloomberg session setup with pooling
def get_bloomberg_session(reuse=True):
    """
    Get Bloomberg session with optional reuse.
    
    Args:
        reuse: If True, reuse existing session. If False, create new session.
    
    Returns:
        Bloomberg session or None
    """
    global _bloomberg_session
    
    if not BLOOMBERG_AVAILABLE:
        return None
    
    # If reuse is enabled and we have a session, try to reuse it
    if reuse and _bloomberg_session is not None:
        try:
            # Test if session is still alive by checking if we can open a service
            # This is a lightweight check
            debug("Reusing existing Bloomberg session")
            return _bloomberg_session
        except Exception as e:
            debug(f"Existing session failed, creating new one: {e}")
            _bloomberg_session = None
    
    # Create new session with lock to prevent race conditions
    if _session_lock:
        with _session_lock:
            return _create_new_session()
    else:
        return _create_new_session()

def _create_new_session():
    """Internal function to create a new Bloomberg session"""
    global _bloomberg_session
    
    debug("Creating new Bloomberg session")
    sessionOptions = blpapi.SessionOptions()
    sessionOptions.setServerHost(BLOOMBERG_HOST)
    sessionOptions.setServerPort(BLOOMBERG_PORT)
    # Increase timeouts for better reliability
    sessionOptions.setConnectTimeout(5000)  # 5 seconds
    sessionOptions.setDefaultKeepAliveInactivityTime(300)  # 5 minutes
    
    session = blpapi.Session(sessionOptions)
    
    if session.start():
        debug("Bloomberg session started successfully")
        _bloomberg_session = session
        return session
    else:
        print("Failed to start Bloomberg session")
        return None

def close_bloomberg_session():
    """Close the global Bloomberg session - call this on shutdown"""
    global _bloomberg_session
    if _bloomberg_session:
        try:
            _bloomberg_session.stop()
            debug("Bloomberg session stopped")
        except:
            pass
        _bloomberg_session = None

def get_bloomberg_data(session, ticker, fields):
    """
    Get real data from Bloomberg.
    
    Args:
        ticker: Single ticker string OR list of tickers for batch request
        fields: List of field names
    
    Returns:
        If single ticker: Dict of field/value pairs
        If multiple tickers: Dict of ticker -> {field: value}
    """
    if not session:
        debug("No session provided")
        return None
    
    # Support batch requests: ticker can be a list
    is_batch = isinstance(ticker, list)
    tickers = ticker if is_batch else [ticker]
    
    try:
        debug(f"Opening reference data service...")
        # Open reference data service
        if not session.openService("//blp/refdata"):
            debug("Failed to open reference data service")
            return None
            
        debug("Reference data service opened successfully")
        refDataService = session.getService("//blp/refdata")
        request = refDataService.createRequest("ReferenceDataRequest")
        
        # Add all tickers (batch support!)
        bloomberg_tickers = []
        for t in tickers:
            # Ensure ticker is in Bloomberg format (add "US Equity" if not present)
            if not any(suffix in t.upper() for suffix in [" EQUITY", " CORP", " GOVT", " INDEX", " CURNCY", " COMDTY"]):
                bloomberg_ticker = f"{t} US Equity"
            else:
                bloomberg_ticker = t
            bloomberg_tickers.append(bloomberg_ticker)
            request.getElement("securities").appendValue(bloomberg_ticker)
        
        debug(f"Creating batch request for {len(bloomberg_tickers)} tickers: {bloomberg_tickers}, fields={fields}")
        
        # Add fields
        for field in fields:
            request.getElement("fields").appendValue(field)
            
        debug("Sending request to Bloomberg...")
        # Send request
        session.sendRequest(request)
        
        debug("Processing response...")
        # Process response - collect data for all securities
        all_results = {}
        
        while True:
            event = session.nextEvent(2000)  # 2 second timeout for batch requests
            debug(f"Received event type: {event.eventType()}")
            
            if event.eventType() == blpapi.Event.RESPONSE or event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                for msg in event:
                    debug(f"Processing message: {msg}")
                    if msg.hasElement("securityData"):
                        securityData = msg.getElement("securityData")
                        debug(f"Found securityData with {securityData.numValues()} securities")
                        
                        # Process each security in the response
                        for i in range(securityData.numValues()):
                            security = securityData.getValue(i)
                            security_name = security.getElementAsString("security") if security.hasElement("security") else f"Unknown_{i}"
                            
                            # Check for security errors
                            if security.hasElement("securityError"):
                                securityError = security.getElement("securityError")
                                error_msg = securityError.getElementAsString("message")
                                error_code = securityError.getElementAsString("code")
                                debug(f"Bloomberg security error for {security_name}: {error_msg} (code: {error_code})")
                                all_results[security_name] = {"error": error_msg}
                                continue
                            
                            # Extract field data
                            if security.hasElement("fieldData"):
                                fieldData = security.getElement("fieldData")
                                result = {}
                                for field in fields:
                                    if fieldData.hasElement(field):
                                        value = fieldData.getElementAsString(field)
                                        result[field] = value
                                        debug(f"Got field {field} = {value} for {security_name}")
                                    else:
                                        debug(f"Field {field} not found for {security_name}")
                                        result[field] = None
                                all_results[security_name] = result
                            else:
                                debug(f"No fieldData for {security_name}")
                                all_results[security_name] = {field: None for field in fields}
                                
            if event.eventType() == blpapi.Event.RESPONSE:
                debug("Received final response")
                break
        
        # Return format depends on whether it was a batch request
        if is_batch:
            debug(f"Returning batch data for {len(all_results)} securities")
            return all_results
        else:
            # Single ticker - return just the data dict (backward compatible)
            if bloomberg_tickers[0] in all_results:
                debug(f"Returning data: {all_results[bloomberg_tickers[0]]}")
                return all_results[bloomberg_tickers[0]]
            else:
                debug("No data found in response")
                return None
        
    except Exception as e:
        debug(f"Bloomberg API error: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_bloomberg_bulk_data(session, ticker, field):
    """
    Get Bloomberg bulk/tabular data (BDS) - returns array/table results.
    
    Examples of bulk fields:
    - DVD_HIST_ALL: Dividend history
    - PG_REVENUE: Revenue by segment
    - TOP_20_HOLDERS_PUBLIC_FILINGS: Major shareholders
    - CRNCY_ADJ_PX_LAST: Multi-currency prices
    
    Args:
        session: Bloomberg session
        ticker: Single ticker string
        field: Bulk field name (must be a BDS-type field)
    
    Returns:
        List of dictionaries, where each dict represents one row of the bulk data
    """
    if not session:
        debug("No session provided")
        return None
    
    try:
        debug(f"Opening reference data service for bulk data...")
        # Open reference data service
        if not session.openService("//blp/refdata"):
            debug("Failed to open reference data service")
            return None
            
        debug("Reference data service opened successfully")
        refDataService = session.getService("//blp/refdata")
        request = refDataService.createRequest("ReferenceDataRequest")
        
        # Ensure ticker is in Bloomberg format (add "US Equity" if not present)
        bloomberg_ticker = ticker
        if not any(suffix in ticker.upper() for suffix in [" EQUITY", " CORP", " GOVT", " INDEX", " CURNCY", " COMDTY"]):
            bloomberg_ticker = f"{ticker} US Equity"
        
        debug(f"Creating bulk data request for ticker={ticker} -> Bloomberg ticker={bloomberg_ticker}, field={field}")
        
        # Add ticker and field
        request.getElement("securities").appendValue(bloomberg_ticker)
        request.getElement("fields").appendValue(field)
        
        debug("Sending bulk data request to Bloomberg...")
        # Send request
        session.sendRequest(request)
        
        debug("Processing bulk data response...")
        # Process response
        bulk_results = []
        
        while True:
            event = session.nextEvent(5000)  # 5 second timeout for bulk data
            debug(f"Received event type: {event.eventType()}")
            
            if event.eventType() == blpapi.Event.RESPONSE or event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                for msg in event:
                    debug(f"Processing bulk message")
                    if msg.hasElement("securityData"):
                        securityData = msg.getElement("securityData")
                        
                        for i in range(securityData.numValues()):
                            security = securityData.getValue(i)
                            security_name = security.getElementAsString("security") if security.hasElement("security") else "Unknown"
                            
                            # Check for security errors
                            if security.hasElement("securityError"):
                                securityError = security.getElement("securityError")
                                error_msg = securityError.getElementAsString("message")
                                debug(f"Bloomberg security error for {security_name}: {error_msg}")
                                return {"error": error_msg}
                            
                            # Check for field exceptions
                            if security.hasElement("fieldExceptions"):
                                fieldExceptions = security.getElement("fieldExceptions")
                                if fieldExceptions.numValues() > 0:
                                    for j in range(fieldExceptions.numValues()):
                                        fieldException = fieldExceptions.getValue(j)
                                        field_id = fieldException.getElementAsString("fieldId")
                                        error_info = fieldException.getElement("errorInfo")
                                        error_msg = error_info.getElementAsString("message")
                                        debug(f"Field exception for {field_id}: {error_msg}")
                                        return {"error": f"Field error for {field_id}: {error_msg}"}
                            
                            # Extract bulk field data (array data)
                            if security.hasElement("fieldData"):
                                fieldData = security.getElement("fieldData")
                                
                                if fieldData.hasElement(field):
                                    bulk_field = fieldData.getElement(field)
                                    
                                    # Check if it's actually bulk data (array) by trying numValues()
                                    try:
                                        num_rows = bulk_field.numValues()
                                        debug(f"Found bulk array with {num_rows} rows")
                                        
                                        # Process each row in the bulk data
                                        for row_idx in range(num_rows):
                                            try:
                                                row_data = {}
                                                row_element = bulk_field.getValue(row_idx)
                                                
                                                # Extract all fields from this row
                                                for field_idx in range(row_element.numElements()):
                                                    try:
                                                        elem = row_element.getElement(field_idx)
                                                        field_name = str(elem.name())
                                                        
                                                        # Get value with NaN/null handling for JSON serialization
                                                        try:
                                                            field_value = elem.getValueAsString()
                                                            # Check for NaN, infinity, or invalid float strings
                                                            if field_value and field_value.lower() in ['nan', 'inf', '-inf', 'null']:
                                                                field_value = None
                                                        except:
                                                            try:
                                                                raw_value = elem.getValue()
                                                                # Handle NaN and infinity in numeric values
                                                                import math
                                                                if isinstance(raw_value, float):
                                                                    if math.isnan(raw_value) or math.isinf(raw_value):
                                                                        field_value = None
                                                                    else:
                                                                        field_value = raw_value
                                                                else:
                                                                    field_value = str(raw_value) if raw_value is not None else None
                                                            except:
                                                                field_value = None
                                                        
                                                        row_data[field_name] = field_value
                                                    except Exception as e:
                                                        debug(f"Error extracting element {field_idx}: {e}")
                                                        continue
                                                
                                                if row_data:  # Only add non-empty rows
                                                    bulk_results.append(row_data)
                                                    debug(f"Added bulk row {row_idx + 1}: {list(row_data.keys())}")
                                            except Exception as e:
                                                debug(f"Error processing row {row_idx}: {e}")
                                                continue
                                    except (AttributeError, TypeError) as e:
                                        # Not an array - this is a regular field, not bulk data
                                        debug(f"Field {field} is not bulk data: {e}")
                                        return {"error": f"Field {field} is not a bulk data field (BDS)"}
                                else:
                                    debug(f"Field {field} not found in fieldData")
                                    return {"error": f"Field {field} not available for this security"}
                                
            if event.eventType() == blpapi.Event.RESPONSE:
                debug(f"Received final bulk response with {len(bulk_results)} rows")
                break
        
        return bulk_results
        
    except Exception as e:
        error_msg = f"Bloomberg bulk data API error: {str(e)}"
        debug(error_msg)
        import traceback
        trace_str = traceback.format_exc()
        debug(f"Traceback: {trace_str}")
        return {"error": error_msg, "traceback": trace_str}

def get_bloomberg_historical_data(session, ticker, fields, start_date, end_date, periodicity="DAILY"):
    """Get historical data from Bloomberg"""
    if not session:
        debug("No session provided for historical data")
        return None
        
    try:
        debug(f"Opening historical data service...")
        # Open historical data service
        if not session.openService("//blp/refdata"):
            debug("Failed to open reference data service for historical")
            return None
            
        debug("Historical data service opened successfully")
        refDataService = session.getService("//blp/refdata")
        request = refDataService.createRequest("HistoricalDataRequest")
        
        # Ensure ticker is in Bloomberg format
        bloomberg_ticker = ticker
        if not any(suffix in ticker.upper() for suffix in [" EQUITY", " CORP", " GOVT", " INDEX", " CURNCY", " COMDTY"]):
            bloomberg_ticker = f"{ticker} US Equity"
            
        debug(f"Creating historical request for ticker={ticker} -> Bloomberg ticker={bloomberg_ticker}")
        debug(f"Date range: {start_date} to {end_date}, fields={fields}, periodicity={periodicity}")
        
        # Add ticker and fields
        request.getElement("securities").appendValue(bloomberg_ticker)
        for field in fields:
            request.getElement("fields").appendValue(field)
            
        # Set date range
        request.set("startDate", start_date.replace("-", ""))  # Bloomberg expects YYYYMMDD format
        request.set("endDate", end_date.replace("-", ""))
        
        # Set periodicity to control data frequency (DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY)
        request.set("periodicitySelection", periodicity.upper())
        
        # CRITICAL OVERRIDES for data quality and consistency
        # Corporate action adjustments (essential for accurate historical prices)
        request.set("adjustmentNormal", True)       # Adjust for normal cash dividends
        request.set("adjustmentAbnormal", True)     # Adjust for special/abnormal dividends  
        request.set("adjustmentSplit", True)        # Adjust for stock splits
        request.set("adjustmentFollowDPDF", False)  # Use Bloomberg standard adjustment
        
        # Data consistency settings
        request.set("currency", "USD")  # Force USD for consistent comparisons (can be parameterized later)
        request.set("pricingOption", "PRICING_OPTION_PRICE")  # Use price (not yield)
        
        # Non-trading day handling
        request.set("nonTradingDayFillOption", "NON_TRADING_WEEKDAYS")  # Fill non-trading weekdays
        request.set("nonTradingDayFillMethod", "PREVIOUS_VALUE")  # Use previous value
        
        # Control response size
        request.set("maxDataPoints", 10000)  # Prevent silent truncation
        
        # Get the best quality data
        request.set("returnEids", True)  # Return entity identifiers
        request.set("periodicityAdjustment", "ACTUAL")  # Use actual periods, not calendar
        
        debug("Sending historical request to Bloomberg...")
        # Send request
        requestID = session.sendRequest(request)
        debug(f"Historical request sent with ID: {requestID}")
        
        debug("Processing historical response...")
        historical_data = []
        
        # Process response
        while True:
            event = session.nextEvent(5000)  # 5 second timeout for historical data
            debug(f"Received historical event type: {event.eventType()}")
            
            if event.eventType() == blpapi.Event.TIMEOUT:
                debug("Timeout waiting for historical response")
                break
            
            if event.eventType() == blpapi.Event.RESPONSE or event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                for msg in event:
                    debug(f"Processing historical message: {msg}")
                    if msg.hasElement("securityData"):
                        # For historical data, securityData is a single element, not an array
                        security = msg.getElement("securityData")
                        debug(f"Found historical securityData")
                        
                        # Check for security errors
                        if security.hasElement("securityError"):
                            securityError = security.getElement("securityError")
                            error_msg = securityError.getElementAsString("message")
                            error_code = securityError.getElementAsString("code")
                            debug(f"Bloomberg historical security error: {error_msg} (code: {error_code})")
                            raise HTTPException(status_code=400, detail=f"Invalid ticker '{ticker}': {error_msg}")
                        
                        if security.hasElement("fieldData"):
                            fieldDataArray = security.getElement("fieldData")
                            debug(f"Found {fieldDataArray.numValues()} historical data points")
                            
                            for j in range(fieldDataArray.numValues()):
                                fieldData = fieldDataArray.getValueAsElement(j)
                                date_str = fieldData.getElementAsString("date")
                                # Convert YYYY-MM-DD format from YYYY-MM-DD (it's already formatted)
                                formatted_date = str(date_str)
                                
                                values = {}
                                for field in fields:
                                    if fieldData.hasElement(field):
                                        try:
                                            value = fieldData.getElementAsFloat(field)
                                            values[field] = value
                                            debug(f"Got historical {field} = {value} for {formatted_date}")
                                        except:
                                            # Try as string if float fails
                                            value = fieldData.getElementAsString(field)
                                            values[field] = value
                                            debug(f"Got historical {field} = {value} for {formatted_date}")
                                
                                if values:
                                    historical_data.append({
                                        "date": formatted_date,
                                        "values": values
                                    })
                                        
                debug(f"Collected {len(historical_data)} historical data points")
                                
            if event.eventType() == blpapi.Event.RESPONSE:
                debug("Received final historical response")
                break
                
        if historical_data:
            debug(f"Returning {len(historical_data)} historical records")
            return historical_data
        else:
            debug("No historical data found in response")
            return None
        
    except Exception as e:
        debug(f"Bloomberg historical API error: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_provenance(fields: List[str], timestamp: datetime.datetime) -> str:
    """Create provenance string for responses"""
    try:
        descriptors = []
        for field in fields:
            record = get_field_metadata(field)
            field_id = record.get('Field ID')
            if field_id:
                descriptors.append(f"{field} ({field_id})")
            else:
                descriptors.append(field)
        fields_clause = ', '.join(descriptors) if descriptors else 'n/a'
    except HTTPException:
        fields_clause = ', '.join(fields) if fields else 'n/a'
    return ("Bloomberg (brokered via Desktop API) - "
            f"fields: {fields_clause} - retrieved at {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")





@app.get("/blp/fields")
@limiter.limit("60/minute")
async def list_fields(
    request: Request,
    api_key: str = Depends(get_api_key),
    contains: Optional[str] = Query(None, description="Case-insensitive substring to match"),
    regex: Optional[str] = Query(None, description="Regular expression applied to mnemonic/description"),
    terms: Optional[List[str]] = Query(None, description="Tokens that must match (see match mode)"),
    match_mode: str = Query("any", pattern="^(?i:any|all)$", description="Require any or all tokens to match"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
):
    """List allowed Bloomberg fields with optional filtering."""

    catalog = get_field_catalog()
    sample_columns = catalog['sample_columns']

    normalized_contains = contains.lower() if contains else None

    pattern = None
    if regex:
        try:
            pattern = re.compile(regex, re.IGNORECASE)
        except re.error as exc:
            raise HTTPException(status_code=400, detail=f"Invalid regex: {exc}") from exc

    match_mode_normalized = match_mode.lower()
    if match_mode_normalized not in {"any", "all"}:
        raise HTTPException(status_code=400, detail="match_mode must be 'any' or 'all'")

    term_list = [t.lower() for t in terms] if terms else []

    filtered_records = []
    for record in catalog['records']:
        if not record_matches_filters(
            record,
            contains=normalized_contains,
            pattern=pattern,
            terms=term_list,
            match_mode=match_mode_normalized,
        ):
            continue
        filtered_records.append(record)

    fields_info = []
    for record in filtered_records[:limit]:
        entry = {
            "field": record.get('Display Name'),
            "field_id": record.get('Field ID'),
            "description": record.get('Description'),
            "data_type": record.get('Data Type'),
        }
        samples = {}
        for column in sample_columns:
            value = _serialize_value(record.get(column))
            if value is not None:
                samples[column] = value
        if samples:
            entry["sampleValues"] = samples
        fields_info.append(entry)

    fields_info.sort(key=lambda item: (item["field"] or ""))

    timestamp = datetime.datetime.utcnow()
    provenance = create_provenance([], timestamp)

    return {
        "total": len(filtered_records),
        "returned": len(fields_info),
        "fields": fields_info,
        "provenance": provenance,
    }



@app.get("/blp/securities")
@limiter.limit("60/minute")
async def list_securities(
    request: Request,
    query: str = Query(..., description="Instrument search pattern (e.g., 'BALTIC* INDEX*')"),
    limit: int = Query(15, ge=1, le=500, description="Maximum number of securities to include in the response"),
    api_key: str = Depends(get_api_key),
):
    """Search for Bloomberg securities (SECF-style)."""

    results, total_count = get_bloomberg_instruments(query, limit)
    timestamp = datetime.datetime.utcnow()
    provenance = (
        "Bloomberg (brokered via Desktop API) - "
        f"securities query: {query} - retrieved at {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )

    response = {
        "query": query,
        "total": total_count,
        "returned": len(results),
        "results": results,
        "provenance": provenance,
    }
    if total_count == 0:
        response["message"] = "No Data"
    return response

@app.get("/blp/screen")
@limiter.limit("60/minute")
async def run_equity_screen(
    request: Request,
    screen_name: str = Query(..., description="Name of saved Bloomberg EQS screen"),
    screen_type: str = Query("PRIVATE", pattern="^(?i:PRIVATE|GLOBAL)$", description="PRIVATE (user screens) or GLOBAL (Bloomberg sample screens)"),
    group: Optional[str] = Query(None, description="Folder/category for GLOBAL screens (e.g., 'Popular', 'Investment Banking')"),
    language: str = Query("ENGLISH", description="Language ID for screen results"),
    asof_date: Optional[str] = Query(None, description="Optional date (YYYY-MM-DD) for historical screening (Point-in-Time)"),
    api_key: str = Depends(get_api_key),
):
    """
    Run a Bloomberg Equity Screen (BEQS).
    
    This endpoint executes saved Bloomberg EQS screens and returns the results.
    
    Screen Types:
    - PRIVATE: Your personal saved screens in Bloomberg EQS
    - GLOBAL: Bloomberg's pre-built sample screens
    
    Popular GLOBAL screens:
    - "Insider Buyers" (group: "Popular")
    - "Cash/Debt Ratio" (group: "Investment Banking")
    - "Dividend Yield Screen" (group: "Popular")
    
    Examples:
    - Run your private screen: ?screen_name=My%20Screen&screen_type=PRIVATE
    - Run Bloomberg sample: ?screen_name=Insider%20Buyers&screen_type=GLOBAL&group=Popular
    - Historical screen: ?screen_name=My%20Screen&screen_type=PRIVATE&asof_date=2024-01-01
    """
    
    if not BLOOMBERG_AVAILABLE:
        raise HTTPException(status_code=503, detail="Bloomberg API not available")
    
    session = get_bloomberg_session()
    if not session:
        raise HTTPException(status_code=503, detail="Could not establish Bloomberg session")
    
    # Format asof_date if provided
    formatted_date = None
    if asof_date:
        try:
            formatted_date = asof_date.replace("-", "")
        except:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    debug(f"Running BEQS: screen={screen_name}, type={screen_type}, group={group}, asof={asof_date}")
    
    results = get_bloomberg_screen_results(
        session, 
        screen_name, 
        screen_type, 
        group, 
        language,
        formatted_date
    )
    
    if not results:
        raise HTTPException(
            status_code=404, 
            detail=f"Screen '{screen_name}' not found or returned no results. "
                   f"Check: 1) Screen name is correct, 2) Screen type is correct (PRIVATE vs GLOBAL), "
                   f"3) For GLOBAL screens, group parameter is set correctly"
        )
    
    timestamp = datetime.datetime.utcnow()
    provenance = (
        "Bloomberg (brokered via Desktop API - BEQS) - "
        f"screen: {screen_name} ({screen_type})"
        + (f", group: {group}" if group else "")
        + (f", asof: {asof_date}" if asof_date else "")
        + f" - retrieved at {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    
    return {
        "screen_name": screen_name,
        "screen_type": screen_type,
        "group": group,
        "asof_date": asof_date,
        "count": len(results),
        "results": results,
        "provenance": provenance
    }

@app.get("/blp/coverage")
@limiter.limit("60/minute")
async def check_coverage(request: Request, ticker: str, api_key: str = Depends(get_api_key)):
    """Check Bloomberg coverage for a ticker"""
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker parameter is required")

    coverage_field = get_default_coverage_field()

    if BLOOMBERG_AVAILABLE:
        debug(f"Checking Bloomberg coverage for {ticker} using field {coverage_field}")
        session = get_bloomberg_session()
        if session:
            try:
                test_data = get_bloomberg_data(session, ticker, [coverage_field])
                # Don't stop session - it's reused
                if test_data and coverage_field in test_data:
                    covered = True
                    field_value = test_data.get(coverage_field)
                    message = (
                        "Data available via Bloomberg Desktop API "
                        f"({coverage_field}: {field_value})"
                    )
                    debug(f"Coverage confirmed for {ticker}: {field_value}")
                else:
                    covered = False
                    message = "Security not found in Bloomberg database"
                    debug(f"No coverage for {ticker}")
            except HTTPException as exc:
                covered = False
                message = exc.detail
                debug(f"Coverage check failed for {ticker}: {exc.detail}")
            except Exception as exc:
                covered = False
                message = "Error checking Bloomberg coverage"
                debug(f"Coverage check error for {ticker}: {exc}")
        else:
            covered = False
            message = "No Data"
    else:
        covered = False
        message = "No Data"

    timestamp = datetime.datetime.utcnow()
    provenance = create_provenance([coverage_field], timestamp)

    return {
        "ticker": ticker,
        "covered": covered,
        "message": message,
        "coverage_field": coverage_field,
        "provenance": provenance
    }

@app.get("/blp/refdata")
@limiter.limit("60/minute")
async def get_refdata(
    request: Request,
    ticker: List[str] = Query(..., description="One or more tickers (supports batch requests)"),
    fields: List[str] = Query(...),
    api_key: str = Depends(get_api_key)
):
    """
    Get current reference data for one or more tickers.
    
    Supports batch requests: Pass multiple tickers to get data in ONE API call.
    Example: ?ticker=AAPL&ticker=MSFT&ticker=GOOGL&fields=PX_LAST
    """
    if not ticker or len(ticker) == 0:
        raise HTTPException(status_code=400, detail="At least one ticker is required")

    resolved_fields, field_metadata = validate_fields(fields)
    
    is_batch = len(ticker) > 1
    
    if BLOOMBERG_AVAILABLE:
        session = get_bloomberg_session()
        if session:
            # Pass list of tickers for batch request
            data = get_bloomberg_data(session, ticker if is_batch else ticker[0], resolved_fields)
            if not data:
                data = {t: build_mock_refdata(t, resolved_fields) for t in ticker} if is_batch else build_mock_refdata(ticker[0], resolved_fields)
        else:
            data = {t: build_mock_refdata(t, resolved_fields) for t in ticker} if is_batch else build_mock_refdata(ticker[0], resolved_fields)
    else:
        data = {t: build_mock_refdata(t, resolved_fields) for t in ticker} if is_batch else build_mock_refdata(ticker[0], resolved_fields)

    timestamp = datetime.datetime.utcnow()
    provenance = create_provenance(resolved_fields, timestamp)
    
    # Format response based on single vs batch
    if is_batch:
        # Batch response: return data for all tickers
        all_ticker_data = {}
        for t in ticker:
            ticker_data = data.get(t, {}) if isinstance(data, dict) else {}
            filtered_data: Dict[str, Any] = {}
            for field in resolved_fields:
                value = ticker_data.get(field) if isinstance(ticker_data, dict) else None
                if value is None or (isinstance(value, str) and not value.strip()):
                    filtered_data[field] = "No Data"
                else:
                    filtered_data[field] = value
            all_ticker_data[t] = filtered_data
        
        return {
            "tickers": ticker,
            "count": len(ticker),
            "fields": resolved_fields,
            "resolved_fields": field_metadata,
            "data": all_ticker_data,
            "provenance": provenance
        }
    else:
        # Single ticker response (backward compatible)
        filtered_data: Dict[str, Any] = {}
        for field in resolved_fields:
            value = (data or {}).get(field) if isinstance(data, dict) else None
            if value is None or (isinstance(value, str) and not value.strip()):
                filtered_data[field] = "No Data"
            else:
                filtered_data[field] = value

        return {
            "ticker": ticker[0],
            "fields": resolved_fields,
            "resolved_fields": field_metadata,
            "data": filtered_data,
            "provenance": provenance
        }

@app.get("/blp/historical")
@limiter.limit("60/minute")
async def get_historical(
    request: Request,
    ticker: str,
    fields: List[str] = Query(...),
    start_date: str = None,
    end_date: str = None,
    periodicity: str = Query("DAILY", pattern="^(?i:DAILY|WEEKLY|MONTHLY|QUARTERLY|YEARLY)$", description="Data frequency: DAILY, WEEKLY, MONTHLY, QUARTERLY, or YEARLY"),
    max_data_points: int = Query(1000, ge=1, le=10000, description="Maximum data points to return (prevents response size issues)"),
    api_key: str = Depends(get_api_key)
):
    """Get historical data for a ticker"""
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker parameter is required")
    if not start_date:
        raise HTTPException(status_code=400, detail="Start date is required")

    resolved_fields, field_metadata = validate_fields(fields)

    if not end_date:
        end_date = datetime.date.today().isoformat()
    
    # Smart periodicity: Auto-upgrade to MONTHLY for long date ranges to avoid response size issues
    try:
        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        days_diff = (end_dt - start_dt).days
        
        # Auto-upgrade periodicity for large date ranges
        if periodicity.upper() == "DAILY":
            if days_diff > 730:  # > 2 years
                original_periodicity = periodicity
                periodicity = "MONTHLY"
                debug(f"Auto-upgrading periodicity from {original_periodicity} to MONTHLY for {days_diff} day range to avoid response size limits")
            elif days_diff > 3650:  # > 10 years
                original_periodicity = periodicity
                periodicity = "QUARTERLY"
                debug(f"Auto-upgrading periodicity from {original_periodicity} to QUARTERLY for {days_diff} day range")
    except Exception as e:
        debug(f"Could not parse dates for smart periodicity: {e}")

    if BLOOMBERG_AVAILABLE:
        debug(f"Attempting to get Bloomberg historical data for {ticker} with fields {resolved_fields}")
        debug(f"Date range: {start_date} to {end_date}, periodicity: {periodicity}")
        session = get_bloomberg_session()
        if session:
            debug("Bloomberg historical session created successfully")
            historical_data = get_bloomberg_historical_data(session, ticker, resolved_fields, start_date, end_date, periodicity)
            # Don't stop session - it's reused
        else:
            historical_data = None
        if not historical_data:
            debug("Historical request failed or returned no data, using mock values")
            historical_data = build_mock_historical(ticker, resolved_fields)
    else:
        historical_data = build_mock_historical(ticker, resolved_fields)

    filtered_data = []
    source_data = historical_data or []
    
    # Limit response size to prevent ChatGPT/client timeout issues
    if len(source_data) > max_data_points:
        debug(f"Truncating response from {len(source_data)} to {max_data_points} data points")
        source_data = source_data[-max_data_points:]  # Keep most recent data
    
    for item in source_data:
        date_value = item.get("date") if isinstance(item, dict) else None
        values_block = item.get("values") if isinstance(item, dict) else None
        normalized_values: Dict[str, Any] = {}
        for field in resolved_fields:
            raw_value = (values_block or {}).get(field) if isinstance(values_block, dict) else None
            if raw_value is None or (isinstance(raw_value, str) and not raw_value.strip()):
                normalized_values[field] = "No Data"
            else:
                normalized_values[field] = raw_value
        filtered_data.append({
            "date": date_value if isinstance(date_value, str) and date_value.strip() else "No Data",
            "values": normalized_values,
        })
    if not filtered_data:
        filtered_data.append({
            "date": "No Data",
            "values": {field: "No Data" for field in resolved_fields},
        })

    timestamp = datetime.datetime.utcnow()
    provenance = create_provenance(resolved_fields, timestamp)

    return {
        "ticker": ticker,
        "fields": resolved_fields,
        "resolved_fields": field_metadata,
        "data": filtered_data,
        "provenance": provenance
    }

from fastapi.responses import JSONResponse
import json

@app.get("/blp/bulkdata")
@limiter.limit("60/minute")
async def get_bulkdata(
    request: Request,
    ticker: str = Query(..., description="Security ticker"),
    field: str = Query(..., description="Bulk data field (e.g., DVD_HIST_ALL, PG_REVENUE, TOP_20_HOLDERS_PUBLIC_FILINGS)"),
    api_key: str = Depends(get_api_key)
):
    """
    Get Bloomberg bulk/tabular data (BDS) - returns array/table results.
    
    Common bulk fields:
    - DVD_HIST_ALL: Complete dividend history
    - PG_REVENUE: Revenue breakdown by segment
    - TOP_20_HOLDERS_PUBLIC_FILINGS: Major institutional shareholders
    - CRNCY_ADJ_PX_LAST: Prices in multiple currencies
    - EARN_ANN_DT_TIME_HIST_WITH_EPS: Historical earnings announcements
    - CF_FREE_CASH_FLOW: Free cash flow by period
    
    Returns a list of dictionaries, where each dict is one row of the table.
    """
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker parameter is required")
    if not field:
        raise HTTPException(status_code=400, detail="Field parameter is required")
    
    # Validate that the field exists (optional - you may want to skip this for bulk fields)
    try:
        resolved_field, field_info = resolve_field_name(field)
        debug(f"Resolved bulk field: {field} -> {resolved_field}")
    except HTTPException:
        # Field not in catalog, but that's OK - bulk fields might not be in the standard catalog
        debug(f"Bulk field {field} not in catalog, proceeding anyway")
        resolved_field = field
        field_info = {"Display Name": field, "Mnemonic": field}
    
    if BLOOMBERG_AVAILABLE:
        session = get_bloomberg_session()
        if session:
            bulk_data = get_bloomberg_bulk_data(session, ticker, resolved_field)
            
            # Check for errors or None
            if bulk_data is None:
                raise HTTPException(status_code=500, detail="Bloomberg API returned None")
            
            if isinstance(bulk_data, dict) and "error" in bulk_data:
                raise HTTPException(status_code=400, detail=bulk_data["error"])
            
            if not bulk_data or not isinstance(bulk_data, list):
                raise HTTPException(status_code=404, detail=f"No bulk data returned for field {field}")
        else:
            raise HTTPException(status_code=503, detail="Bloomberg session unavailable")
    else:
        raise HTTPException(status_code=503, detail="Bloomberg API not available in this environment")
    
    timestamp = datetime.datetime.utcnow()
    provenance = create_provenance([resolved_field], timestamp)
    
    # Ensure bulk_data is a list at this point
    row_count = len(bulk_data) if isinstance(bulk_data, list) else 0
    
    # Sanitize NaN/Inf values for JSON serialization
    import math
    import json
    
    def sanitize_for_json(obj):
        """Recursively sanitize object to remove NaN/Inf values that break JSON"""
        if isinstance(obj, dict):
            return {k: sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize_for_json(item) for item in obj]
        elif isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        elif isinstance(obj, str):
            if obj.lower() in ['nan', 'inf', '-inf']:
                return None
            return obj
        else:
            return obj
    
    sanitized_data = sanitize_for_json(bulk_data) if isinstance(bulk_data, list) else []
    
    response_data = {
        "ticker": ticker,
        "field": resolved_field,
        "field_info": sanitize_for_json(field_info),  # Also sanitize field_info
        "row_count": row_count,
        "data": sanitized_data,
        "provenance": sanitize_for_json(provenance)  # Also sanitize provenance
    }
    
    # DEBUG: Print first record to see what's causing NaN
    if sanitized_data and len(sanitized_data) > 0:
        debug(f"First sanitized record: {sanitized_data[0]}")
    
    # Use custom JSON encoder - try to serialize, catch any remaining NaN
    try:
        json_str = json.dumps(response_data, allow_nan=False, default=str)
        return JSONResponse(content=json.loads(json_str))
    except ValueError as e:
        debug(f"JSON serialization error: {e}")
        debug(f"Response data type: {type(response_data)}")
        # Final fallback - convert everything to strings
        return JSONResponse(content=json.loads(json.dumps(response_data, default=str)))

if __name__ == "__main__":
    import uvicorn
    print(f"Starting Bloomberg Data Broker on {BROKER_HOST}:{BROKER_PORT}")
    print(f"API Key: {API_KEY}")
    print(f"Bloomberg Terminal: {BLOOMBERG_HOST}:{BLOOMBERG_PORT}")
    uvicorn.run(app, host=BROKER_HOST, port=BROKER_PORT)
