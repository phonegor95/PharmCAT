#!/usr/bin/env python3
"""Author UNREVIEWED Gemini translation drafts; never apply them to resources.

Requires an explicit model and approved glossary. google-genai is optional until
an actual request is needed. --help and offline mock tests use only the stdlib.
Outputs (including .provenance.json) are exclusive-create, never overwritten.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys

import pgcore

DEFAULT_PROMPT = Path(__file__).parent / 'prompts/gemini-review-todo-v1.md'
ROOT = Path(__file__).resolve().parents[3]
CACHE_VERSION = 1
GENERATION_CONFIG = {'temperature': 0, 'response_mime_type': 'application/json'}
REQUIRED = {'kind', 'en', 'cn'}
HINTS = {'hint_en', 'hint_cn', 'hint_similarity'}


class InvalidDraft(ValueError):
    """Malformed response or failure of a mechanical fidelity check."""


class RequestFailed(RuntimeError):
    """Sanitized actionable error; never includes an SDK exception body."""


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     allow_nan=False).encode('utf-8')).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidDraft('duplicate JSON key')
        result[key] = value
    return result


def reject_constant(_value):
    raise InvalidDraft('non-finite JSON number')


def parse_json(text):
    try:
        return json.loads(text, object_pairs_hook=unique_object,
                          parse_constant=reject_constant)
    except (ValueError, TypeError):
        raise InvalidDraft('expected strict JSON, without fences or commentary') from None


def validate_todo(items):
    if type(items) is not list:
        raise InvalidDraft('todo must be a JSON array')
    for i, item in enumerate(items):
        if (type(item) is not dict or not REQUIRED <= item.keys()
                or item.keys() - REQUIRED - HINTS):
            raise InvalidDraft(f'item {i}: expected kind/en/cn and optional hint fields only')
        if any(type(item[k]) is not str for k in REQUIRED):
            raise InvalidDraft(f'item {i}: kind/en/cn must be strings')
        if item['kind'] not in ('text', 'impl'):
            raise InvalidDraft(f'item {i}: kind must be text or impl')
        for key in ('hint_en', 'hint_cn'):
            if key in item and type(item[key]) is not str:
                raise InvalidDraft(f'item {i}: {key} must be a string')
        if 'hint_similarity' in item:
            value = item['hint_similarity']
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                raise InvalidDraft(f'item {i}: hint_similarity must be a finite number in [0, 1]')


def validate_literals(item):
    """Conservative draft checks, not a substitute for verify.py or human review."""
    en, cn = item['en'], item['cn']
    if not cn.strip():
        return  # Explicitly unresolved; never cache this as a translation.
    if [m.group(0) for m in pgcore.TAG_FULL.finditer(en)] != [
            m.group(0) for m in pgcore.TAG_FULL.finditer(cn)]:
        raise InvalidDraft('ordered literal HTML tags/attributes changed')
    if Counter(pgcore.ENTITY.findall(en)) != Counter(pgcore.ENTITY.findall(cn)):
        raise InvalidDraft('literal HTML entities changed')
    if pgcore.tag_balance(cn) and not pgcore.tag_balance(en):
        raise InvalidDraft('broken HTML nesting')
    if pgcore.needs_translation(en) and not pgcore.HAN.search(cn):
        raise InvalidDraft('substantive translation has no Chinese text')
    # Keep exact numbers and common identifiers, including additions. Deliberately
    # stricter than verify.py's approved legacy lexicalization exceptions.
    patterns = [r'\d+(?:\.\d+)?',
                r'(?<![A-Za-z0-9_])(?:[A-Z][A-Z0-9-]*\d[A-Z0-9-]*|'
                r'HLA-[A-Z]+|TPMT|DPYD|GGCX|BCHE|CFTR|CPIC|DPWG|FDA|PMID)(?![A-Za-z0-9_])',
                r'\*[0-9]+[A-Za-z]?(?::[0-9]+)*', r'rs\d+',
                r'\d+(?:\.\d+)?\s*(?:%|mg|mcg|µg|ng|kg|mL)(?![A-Za-z])',
                r'https?://[^\s<>"\']+', r'\{\{[^{}]*\}\}|\$\{[^{}]*\}']
    for pattern in patterns:
        if Counter(re.findall(pattern, en)) != Counter(re.findall(pattern, cn)):
            raise InvalidDraft('literal number, unit, identifier or placeholder changed')
    prefix = re.match(r'^[A-Z][A-Z0-9-]*: ', en)
    if item['kind'] == 'impl' and prefix and not cn.startswith(prefix.group(0)):
        raise InvalidDraft('implication gene prefix changed')


def validate_response(source, response):
    validate_todo(response)
    if len(source) != len(response):
        raise InvalidDraft('response count changed')
    for i, (before, after) in enumerate(zip(source, response)):
        if before.keys() != after.keys() or any(
                type(before[k]) is not type(after[k]) or before[k] != after[k]
                for k in before if k != 'cn'):
            raise InvalidDraft(f'item {i}: order, keys, source or hints changed')
        validate_literals(after)
    return response


def cache_key(item):
    # Exact source (no markup/whitespace normalization); hints affect generation.
    return digest({k: v for k, v in item.items() if k != 'cn'})


def make_generate():
    """Only called by executing CLI work, never on import or --help."""
    key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not key:
        raise RequestFailed('Set GEMINI_API_KEY or GOOGLE_API_KEY before requesting a draft.')
    try:
        from google import genai
    except ImportError:
        raise RequestFailed('Optional dependency missing: install google-genai in your authoring environment.') from None
    try:
        client = genai.Client(api_key=key)
    except Exception:
        raise RequestFailed('Gemini client initialization failed; check SDK configuration and credentials.') from None

    def generate(**kwargs):
        return client.models.generate_content(**kwargs).text
    return generate


def request(generate, model, items, prompt, glossary):
    try:
        text = generate(model=model,
                        contents=json.dumps({'glossary': glossary, 'todo': items}, ensure_ascii=False),
                        config={**GENERATION_CONFIG, 'system_instruction': prompt})
    except Exception:
        # Do not log exception strings: provider errors can echo keys or payloads.
        # Request failures must not fan out into single-item retries.
        raise RequestFailed('Gemini request failed; check credentials, model access, quota and network. '
                            'No automatic network retry; rerun with new output paths after resolving it.') from None
    return validate_response(items, parse_json(text))


def translate(items, model, prompt, glossary, batch_size, entries, generate):
    draft = [dict(item) for item in items]
    pending = []
    for i, item in enumerate(items):
        if item['cn'].strip():
            continue  # Never replace a prefilled translation.
        cached = entries.get(cache_key(item))
        if cached is not None:
            candidate = {**item, 'cn': cached}
            validate_response([item], [candidate])
            if not cached.strip():
                raise InvalidDraft('cache contains blank translation')
            draft[i] = candidate
        else:
            pending.append(i)
    if pending and generate is None:
        generate = make_generate()
    for start in range(0, len(pending), batch_size):
        indices = pending[start:start + batch_size]
        batch = [items[i] for i in indices]
        try:
            translated = request(generate, model, batch, prompt, glossary)
        except InvalidDraft:
            if len(batch) == 1:
                translated = [{**batch[0], 'cn': ''}]
            else:
                translated = []
                for item in batch:
                    try:
                        translated.extend(request(generate, model, [item], prompt, glossary))
                    except InvalidDraft:
                        translated.append({**item, 'cn': ''})
        for i, item in zip(indices, translated):
            draft[i] = item
            if item['cn'].strip():
                entries[cache_key(item)] = item['cn']
    return draft


def protect_paths(inputs, outputs):
    """No resource destinations, aliases, symlinks, or overwrite switches."""
    paths = [p.resolve() for p in inputs + outputs]
    if len(paths) != len(set(paths)):
        raise ValueError('input/output/cache/provenance paths must all be distinct')
    resources = ROOT / 'src/main/resources'
    for path in outputs:
        if path.exists() or path.is_symlink():
            raise ValueError('output/cache/provenance already exists; choose new scratch paths')
        if resources == path.resolve() or resources in path.resolve().parents:
            raise ValueError('draft/cache/provenance must not be written into application resources')
        if not path.parent.is_dir():
            raise ValueError('create output parent directories before running')


def write_new(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')


def main(argv=None, *, generate=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--todo', type=Path, required=True)
    ap.add_argument('--glossary', type=Path, required=True, help='approved JSON string-to-string mapping')
    ap.add_argument('--model', required=True, help='explicit Gemini model ID; no floating default')
    ap.add_argument('--output', type=Path, required=True, help='NEW unreviewed draft JSON; never applied')
    ap.add_argument('--prompt', type=Path, default=DEFAULT_PROMPT, help='system instructions (default: %(default)s)')
    ap.add_argument('--batch-size', type=int, default=10)
    ap.add_argument('--cache', type=Path, help='optional NEW cache output; never modifies an existing cache')
    ap.add_argument('--cache-input', type=Path, help='optional read-only versioned draft cache, not translation memory')
    args = ap.parse_args(argv)
    try:
        if args.batch_size < 1 or not args.model.strip():
            raise ValueError('batch-size must be positive and model must be nonblank')
        sidecar = Path(str(args.output) + '.provenance.json')
        inputs = [args.todo, args.glossary, args.prompt] + ([args.cache_input] if args.cache_input else [])
        outputs = [args.output, sidecar] + ([args.cache] if args.cache else [])
        protect_paths(inputs, outputs)
        todo_bytes = args.todo.read_bytes()
        items = parse_json(todo_bytes.decode('utf-8'))
        validate_todo(items)
        approved = parse_json(args.glossary.read_text(encoding='utf-8'))
        if type(approved) is not dict or any(type(k) is not str or type(v) is not str
                                           for k, v in approved.items()):
            raise ValueError('glossary must be a JSON string-to-string mapping')
        glossary = {'approved': approved, 'canonical': pgcore.CANONICAL}
        prompt = args.prompt.read_text(encoding='utf-8')
        if not prompt.strip():
            raise ValueError('prompt must not be blank')
        context = {'version': CACHE_VERSION, 'model': args.model,
                   'config': {**GENERATION_CONFIG, 'batch_size': args.batch_size},
                   'prompt_sha256': hashlib.sha256(prompt.encode('utf-8')).hexdigest(),
                   'glossary_sha256': digest(glossary)}
        entries = {}
        if args.cache_input:
            cache = parse_json(args.cache_input.read_text(encoding='utf-8'))
            if (type(cache) is not dict or set(cache) != {'context', 'review_status', 'entries'}
                    or type(cache['context']) is not dict
                    or type(cache['context'].get('version')) is not int
                    or cache['context']['version'] != CACHE_VERSION
                    or cache['review_status'] != 'unreviewed_draft'
                    or type(cache['entries']) is not dict
                    or any(type(v) is not str or not v.strip() for v in cache['entries'].values())):
                raise ValueError('unsupported/malformed draft cache; legacy source-only caches are not accepted')
            if cache['context'] == context:
                entries = dict(cache['entries'])
        draft = translate(items, args.model, prompt, glossary, args.batch_size, entries, generate)
        unresolved = [i for i, item in enumerate(draft) if not item['cn'].strip()]
        # Recheck after requests; exclusive creation also prevents racing overwrites.
        protect_paths(inputs, outputs)
        write_new(args.output, draft)
        write_new(sidecar, {**context, 'prompt_file': args.prompt.name,
                           'created_utc': datetime.now(timezone.utc).isoformat(),
                           'input_sha256': hashlib.sha256(todo_bytes).hexdigest(),
                           'output_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
                           'review_status': 'unreviewed_draft', 'unresolved_indices': unresolved})
        if args.cache:
            write_new(args.cache, {'context': context, 'review_status': 'unreviewed_draft', 'entries': entries})
        print(f'UNREVIEWED draft: {len(draft)} items; {len(unresolved)} unresolved (zero-based indices: {unresolved}).')
        print('Human bilingual and clinical review required before a separate apply.py invocation.')
        return 2 if unresolved else 0
    except (OSError, ValueError, RequestFailed):
        # Only our own validation/request messages are safe; OSError filenames or
        # parser messages can contain arbitrary input. Report those generically.
        exc = sys.exc_info()[1]
        if isinstance(exc, (InvalidDraft, RequestFailed)) or type(exc) is ValueError:
            print(f'ERROR: {exc}', file=sys.stderr)
        else:
            print('ERROR: file read/write failed; check paths, UTF-8 encoding and permissions.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
