"""
Broader Bloomberg Field Search (//blp/apiflds)

Usage examples:
  - python scripts/field_search_india.py "indian inflation"
  - python scripts/field_search_india.py "baltic index" --mode both --top 50

This script fans out a search phrase into multiple tokens (and optional synonyms),
queries the FieldSearchRequest (and optionally CategorizedFieldSearchRequest),
merges results, scores them by match strength, and prints a ranked list of field
mnemonics with descriptions and datatypes.
"""

from __future__ import annotations

import sys
import argparse
import re
from typing import Dict, List, Tuple, Iterable, Set
from collections import Counter
from pathlib import Path

import blpapi
from blpapi import SessionOptions, Session, Event


def init_session(host: str = 'localhost', port: int = 8194) -> Session:
    opts = SessionOptions()
    opts.setServerHost(host)
    opts.setServerPort(port)
    session = Session(opts)
    if not session.start():
        raise SystemExit('Failed to start Bloomberg session')
    if not session.openService('//blp/apiflds'):
        session.stop()
        raise SystemExit('Failed to open //blp/apiflds service')
    return session


def tokenize(query: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+", query.lower())
    return [t for t in tokens if t]


STOPWORDS: Set[str] = set(
    "the a an and or of for to in on by with from at as into over under about across between against without within per"
    .split()
)


def normalize_token(tok: str) -> str:
    return tok.lower()


def extract_tokens(text: str) -> List[str]:
    if not text:
        return []
    toks = re.findall(r"[a-zA-Z][a-zA-Z0-9_]+", text.lower())
    return [t for t in toks if len(t) > 2 and t not in STOPWORDS]


def derive_terms_from_results(results: Dict[str, Dict], exclude: Iterable[str], limit: int) -> List[str]:
    exclude_set = {normalize_token(t) for t in exclude}
    counter: Counter[str] = Counter()
    for rec in results.values():
        for field in ('mnemonic', 'description', 'category'):
            counter.update(extract_tokens(rec.get(field, '')))
    # Boost tokens that appear in mnemonics
    for rec in results.values():
        counter.update({normalize_token(t): 2 for t in extract_tokens(rec.get('mnemonic', ''))})
    cand = [t for t, c in counter.most_common() if t not in exclude_set]
    return cand[: max(0, limit)] if limit > 0 else []


def derive_terms_from_catalog(catalog_path: Path, seed: Iterable[str], limit: int) -> List[str]:
    try:
        import pandas as pd
    except Exception:
        return []
    if not catalog_path.exists():
        return []
    try:
        df = pd.read_excel(catalog_path, sheet_name='Pruned List')
    except Exception:
        return []
    seed_set = {normalize_token(s) for s in seed}
    counter: Counter[str] = Counter()
    for col in ('Display Name', 'Description'):
        if col in df.columns:
            texts = df[col].astype(str).tolist()
            for txt in texts:
                toks = extract_tokens(txt)
                if any(s in toks for s in seed_set):
                    counter.update(toks)
    cand = [t for t, c in counter.most_common() if t not in seed_set]
    return cand[: max(0, limit)] if limit > 0 else []


def _send_and_collect(session: Session, request, term: str, results: Dict[str, Dict]):
    session.sendRequest(request)
    while True:
        event = session.nextEvent(2000)
        et = event.eventType()
        if et in (Event.PARTIAL_RESPONSE, Event.RESPONSE):
            for message in event:
                if message.hasElement('fieldData'):
                    data = message.getElement('fieldData')
                    for entry in data.values():
                        # Each entry should have id, fieldInfo or fieldError
                        field_id = entry.getElementAsString('id') if entry.hasElement('id') else ''
                        if entry.hasElement('fieldInfo'):
                            info = entry.getElement('fieldInfo')
                            mnemonic = info.getElementAsString('mnemonic') if info.hasElement('mnemonic') else field_id
                            desc = info.getElementAsString('description') if info.hasElement('description') else ''
                            dtype = info.getElementAsString('datatype') if info.hasElement('datatype') else ''
                            rec = results.setdefault(mnemonic, {
                                'mnemonic': mnemonic,
                                'id': field_id,
                                'description': desc,
                                'datatype': dtype,
                                'score': 0,
                                'terms': set(),
                                'category': '',
                            })
                            # score by presence of term in mnemonic/description
                            term_l = term.lower()
                            if term_l in (mnemonic or '').lower():
                                rec['score'] += 2
                            if term_l in (desc or '').lower():
                                rec['score'] += 1
                            rec['terms'].add(term)
                        elif entry.hasElement('fieldError'):
                            # ignore errors for now
                            pass
            if et == Event.RESPONSE:
                break
        elif et == Event.TIMEOUT:
            break


def search_fields(session: Session, terms: List[str]) -> Dict[str, Dict]:
    service = session.getService('//blp/apiflds')
    results: Dict[str, Dict] = {}
    for term in terms:
        req = service.createRequest('FieldSearchRequest')
        req.set('searchSpec', term)
        # Avoid narrowing filters; let results be broad
        _send_and_collect(session, req, term, results)
    return results


def categorized_search(session: Session, terms: List[str], results: Dict[str, Dict]):
    service = session.getService('//blp/apiflds')
    for term in terms:
        req = service.createRequest('CategorizedFieldSearchRequest')
        req.set('searchSpec', term)
        session.sendRequest(req)
        while True:
            event = session.nextEvent(2000)
            et = event.eventType()
            if et in (Event.PARTIAL_RESPONSE, Event.RESPONSE):
                for message in event:
                    if message.hasElement('category'):
                        cats = message.getElement('category')
                        for cat in cats.values():
                            cat_name = ''
                            try:
                                cat_name = cat.getElementAsString('categoryName') if cat.hasElement('categoryName') else ''
                            except Exception:
                                cat_name = ''
                            if cat.hasElement('fieldData'):
                                fdata = cat.getElement('fieldData')
                                for entry in fdata.values():
                                    field_id = entry.getElementAsString('id') if entry.hasElement('id') else ''
                                    info = entry.getElement('fieldInfo') if entry.hasElement('fieldInfo') else None
                                    if info is None:
                                        continue
                                    mnemonic = info.getElementAsString('mnemonic') if info.hasElement('mnemonic') else field_id
                                    desc = info.getElementAsString('description') if info.hasElement('description') else ''
                                    dtype = info.getElementAsString('datatype') if info.hasElement('datatype') else ''
                                    rec = results.setdefault(mnemonic, {
                                        'mnemonic': mnemonic,
                                        'id': field_id,
                                        'description': desc,
                                        'datatype': dtype,
                                        'score': 0,
                                        'terms': set(),
                                        'category': cat_name,
                                    })
                                    # boost category hits a bit
                                    rec['score'] += 1
                                    rec['terms'].add(term)
            if et == Event.RESPONSE:
                break
            elif et == Event.TIMEOUT:
                break


def matches_terms(rec: Dict, required_terms: List[str], mode: str = 'any') -> bool:
    """Check if a record matches any/all required terms in mnemonic+description."""
    hay = f"{rec.get('mnemonic','')} {rec.get('description','')}".lower()
    if mode == 'all':
        return all(t.lower() in hay for t in required_terms)
    return any(t.lower() in hay for t in required_terms)


def main():
    parser = argparse.ArgumentParser(description='Broadened Bloomberg field search')
    parser.add_argument('query', help='Search phrase, e.g., "indian inflation"')
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=8194)
    parser.add_argument('--mode', choices=['search', 'categorized', 'both'], default='both')
    # Expansion options driven by data (no hard-coded lists)
    parser.add_argument('--expand-from-results', type=int, default=0, metavar='N',
                        help='Derive up to N extra terms from initial search results and re-search')
    parser.add_argument('--expand-from-catalog', type=int, default=0, metavar='N',
                        help='Derive up to N extra terms from the pruned field catalog and re-search')
    parser.add_argument('--catalog-path', type=Path, default=Path('Production Data') / 'Bloomberg Master Field List.xlsx',
                        help='Path to the pruned catalog for expansion (default: Production Data/..xlsx)')
    # Matching/filters
    parser.add_argument('--match', choices=['any', 'all'], default='any',
                        help='Require any/all of the original tokens to be present in results (default any)')
    parser.add_argument('--must', type=str, default='', help='Regex that results must match (mnemonic/description)')
    parser.add_argument('--contains', type=str, default='', help='Substring that results must contain (case-insensitive)')
    parser.add_argument('--top', type=int, default=30, help='Show top N results')
    args = parser.parse_args()

    tokens = tokenize(args.query)
    # Always include original tokens; no built-in synonyms
    terms = list(tokens)
    if not terms:
        print('No valid search terms parsed from query')
        sys.exit(1)

    session = init_session(args.host, args.port)
    try:
        results = {}
        if args.mode in ('search', 'both'):
            rs = search_fields(session, terms)
            results.update(rs)
        if args.mode in ('categorized', 'both'):
            categorized_search(session, terms, results)
        # Data-driven expansion: from results
        if args.expand_from_results > 0:
            extra = derive_terms_from_results(results, exclude=terms, limit=args.expand_from_results)
            for term in extra:
                if term not in terms:
                    terms.append(term)
            if extra:
                # search again with extras
                if args.mode in ('search', 'both'):
                    rs2 = search_fields(session, extra)
                    results.update(rs2)
                if args.mode in ('categorized', 'both'):
                    categorized_search(session, extra, results)

        # Data-driven expansion: from catalog
        if args.expand_from_catalog > 0:
            cat_extra = derive_terms_from_catalog(args.catalog_path, seed=tokens, limit=args.expand_from_catalog)
            for term in cat_extra:
                if term not in terms:
                    terms.append(term)
            if cat_extra:
                if args.mode in ('search', 'both'):
                    rs3 = search_fields(session, cat_extra)
                    results.update(rs3)
                if args.mode in ('categorized', 'both'):
                    categorized_search(session, cat_extra, results)

        # Rank results by score then by mnemonic
        ranked: List[Tuple[str, Dict]] = sorted(results.items(), key=lambda kv: (-kv[1]['score'], kv[0]))

        # Filtering: enforce original tokens presence if requested; regex/contains filters
        filtered: List[Tuple[str, Dict]] = []
        for mnemonic, rec in ranked:
            if args.match and not matches_terms(rec, tokens, args.match):
                continue
            if args.contains and args.contains.lower() not in f"{rec.get('mnemonic','')} {rec.get('description','')}".lower():
                continue
            if args.must:
                try:
                    if not re.search(args.must, f"{rec.get('mnemonic','')} {rec.get('description','')}", re.IGNORECASE):
                        continue
                except re.error:
                    pass
            filtered.append((mnemonic, rec))

        print(f"Query: '{args.query}' -> tokens: {tokens} -> terms used: {terms}")
        print(f"Found {len(filtered)} matching fields (of {len(ranked)} total). Top {min(args.top, len(filtered))}:")
        print('-' * 100)
        print(f"{'Mnemonic':<36} {'ID':<10} {'Type':<10} {'Score':<5} {'Category':<30} Description")
        print('-' * 100)
        for mnemonic, rec in filtered[: args.top]:
            print(f"{mnemonic:<36} {rec.get('id',''):<10} {rec.get('datatype',''):<10} {rec.get('score',0):<5} {rec.get('category','')[:30]:<30} {rec.get('description','')}")
    finally:
        session.stop()


if __name__ == '__main__':
    main()
