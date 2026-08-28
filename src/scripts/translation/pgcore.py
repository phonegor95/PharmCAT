#!/usr/bin/env python3
"""Shared helpers for the prescribing_guidance.json translation workflow.

Only two fields in prescribing_guidance.json are translated:

    guidelines[].recommendations[].text.html
    guidelines[].recommendations[].implications[]

Everything else must stay byte-identical to upstream. Every tool in this
directory relies on that invariant, and verify.py enforces it.
"""
import json
import os
import re
import tempfile
from pathlib import Path

# The active (translated) data file and the untranslated English reference that
# sits beside it. The reference is named for the upstream version it came from.
REPORTER_DIR = Path('src/main/resources/org/pharmgkb/pharmcat/reporter')
GUIDANCE = REPORTER_DIR / 'prescribing_guidance.json'
REFERENCE_GLOB = 'prescribing_guidance.v*.json'

HAN = re.compile(r'[一-鿿]')
ENTITY = re.compile(r'&[a-zA-Z][a-zA-Z0-9]{1,8};|&#\d{1,6};|&#x[0-9a-fA-F]{1,6};')
TAG_NAME = re.compile(r'<(/?)([a-z0-9]+)')
TAG_FULL = re.compile(r'<(/?)([a-z0-9]+)([^>]*?)(/?)>')
BR = re.compile(r'<br\s*/?>')
VOID_TAGS = {'br', 'hr', 'img', 'input', 'meta', 'link'}

# One canonical rendering per term. Enforced by verify.py across the whole file,
# old translations included. Splits that track a distinction the English makes
# are listed in ALLOWED_VARIANTS instead.
CANONICAL = {
    '依利司他': '依利格鲁司他',      # eliglustat (truncated form)
    '依法韦伦': '依法韦仑',          # efavirenz
    '去甲丙咪嗪': '地昔帕明',        # desipramine
    '三环抗抑郁药': '三环类抗抑郁药',  # tricyclic antidepressant
    '血药浓度监测': '治疗药物监测',    # therapeutic drug monitoring
    '初始剂量': '起始剂量',          # initial / starting dose
    '巯基嘌呤': '巯嘌呤',            # mercaptopurine
    # Shared with GenDecoder's structured-field translation dictionaries.
    '布美匹唑': '布瑞哌唑',          # brexpiprazole
    '布美哌唑': '布瑞哌唑',
    '阿布西替尼': '阿布罗替尼',      # abrocitinib
    '月桂酰阿立哌唑': '阿立哌唑月桂酯',  # aripiprazole lauroxil
    '布瓦西坦': '布瑞西坦',          # brivaracetam
    '司维美林': '西维美林',          # cevimeline
    '德鲁索利替尼': '德鲁佐利替尼',  # deuruxolitinib
    '氘代丁苯那嗪': '氘丁苯那嗪',    # deutetrabenazine
    '美克洛嗪': '氯苯甲嗪',          # meclizine
    'MoviPrep': '莫维普',            # zh-cn product name
    '妥拉唑胺': '妥拉磺胺',          # tolazamide
    '甲苯磺丁脲': '妥布他胺',        # tolbutamide
    '活动评分': '活性评分',          # activity score
    '功能正常和降低功能者': '功能正常和功能降低者',
    '野生型': '参考型',              # reference, not necessarily wild type
}

# Text upstream scraped into its own data by accident. Translations are expected
# to leave it out, so the entity and number checks must ignore it rather than
# report the omission as a defect. Add to this list, with the reason, whenever a
# new upstream artifact turns up — do not weaken the checks themselves.
# Numeric fragments that are deliberately lexicalized in Chinese. Keys are
# exact English/Chinese field pairs so an unrelated missing number still fails.
# Keep this list small and explain every entry.
ALLOWED_MISSING_NUMBERS = {
    (
        'CYP2D6: Based on very limited data available for CYP2D6 ultrarapid metabolizers taking atomoxetine, it is unlikely ultrarapid metabolizers would achieve adequate serum concentrations for the intended effect at standard dosing.',
        'CYP2D6: 根据阿托莫西汀超快代谢者非常有限的数据，超快代谢者在标准剂量下不太可能达到预期效果的足够血清浓度。',
    ): {'2': 1, '6': 1},
}

# Drug and metabolite prefixes whose digits are conventionally lexicalized in
# Chinese. The verifier removes only these exact tokens before comparing the
# remaining numbers, leaving all doses, percentages and clinical thresholds
# strict.
LEXICALIZED_NUMBER_TERMS = (
    re.compile(r'(?i)5-fluorouracil'),
    re.compile(r'(?i)6-mercaptopurine'),
    re.compile(r'(?i)6-TGN'),
    re.compile(r'(?i)N-acetyltransferase 2'),
    re.compile(r'(?i)Z-10-hydroxy'),
)


UPSTREAM_ARTIFACTS = [
    # Website footer navigation appended to two DPWG implications (v3.4.0).
    # Carries a "&amp;" that the Chinese therefore does not have.
    re.compile(r'\s*About ClinPGx Acknowledgements FAQ Publications Downloads '
               r'Citing Licensing &amp; Usage Privacy Policy\s*$'),
]


def strip_artifacts(text):
    """Remove known upstream scraping artifacts before comparing EN against CN."""
    for pattern in UPSTREAM_ARTIFACTS:
        text = pattern.sub('', text)
    return text


# Deliberate splits — do NOT collapse these.
ALLOWED_VARIANTS = {
    '三环类抗抑郁药 vs 三环类药物':
        'EN distinguishes "tricyclic antidepressant"/TCA from bare "tricyclic"; '
        'both occur in the same sentences.',
    '慢代谢者 vs 慢代谢型':
        '者 = the person ("poor metabolizers"); 型 = the phenotype category '
        '("phenotype conversion to poor metabolizer", "非慢代谢型患者").',
}


def find_reference(reporter_dir=REPORTER_DIR):
    """Locate the untranslated English reference next to the active file."""
    hits = sorted(Path(reporter_dir).glob(REFERENCE_GLOB))
    if not hits:
        raise SystemExit(f'no {REFERENCE_GLOB} found in {reporter_dir}; the '
                         'English reference is required to build a translation memory')
    if len(hits) > 1:
        raise SystemExit('multiple English references found, keep exactly one: '
                         + ', '.join(p.name for p in hits))
    return hits[0]


def load(path):
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def dump(data, path):
    """Atomically write with upstream's formatting and no final newline."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f'.{path.name}.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as fh:
            fh.write(json.dumps(data, indent=2, ensure_ascii=False))
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def iter_fields(data):
    """Yield (guideline_idx, rec_idx, kind, sub_idx, value) for translated fields.

    kind is 'text' (sub_idx None) or 'impl' (sub_idx = index in implications).
    """
    for gi, g in enumerate(data.get('guidelines', [])):
        for ri, r in enumerate(g.get('recommendations', [])):
            html = (r.get('text') or {}).get('html')
            if html is not None:
                yield gi, ri, 'text', None, html
            for si, imp in enumerate(r.get('implications') or []):
                yield gi, ri, 'impl', si, imp


def set_field(data, gi, ri, kind, si, value):
    r = data['guidelines'][gi]['recommendations'][ri]
    if kind == 'text':
        r['text']['html'] = value
    else:
        r['implications'][si] = value


def pair(en_data, cn_data):
    """Pair English and Chinese field values positionally.

    Both files must have identical structure; a mismatch means the reference is
    for a different version than the active file.
    """
    en = list(iter_fields(en_data))
    cn = list(iter_fields(cn_data))
    if len(en) != len(cn):
        raise SystemExit(f'field-count mismatch: reference has {len(en)}, '
                         f'translation has {len(cn)}. The English reference does not '
                         'match the version of the translated file.')
    for (gi, ri, k, si, ev), (gi2, ri2, k2, si2, cv) in zip(en, cn):
        if (gi, ri, k, si) != (gi2, ri2, k2, si2):
            raise SystemExit(f'structure mismatch at guideline {gi} rec {ri} ({k})')
        yield k, ev, cv


def tag_balance(text):
    """Return a list of nesting problems ([] when the markup is well-formed)."""
    stack, errors = [], []
    for m in TAG_FULL.finditer(text):
        closing, name, _attrs, self_closing = m.groups()
        if name in VOID_TAGS or self_closing:
            continue
        if closing:
            if stack and stack[-1] == name:
                stack.pop()
            else:
                errors.append(f'unexpected </{name}>')
        else:
            stack.append(name)
    if stack:
        errors.append('unclosed: ' + ','.join(stack))
    return errors


def unescaped(text):
    """Count HTML-special characters left unescaped in text content."""
    stripped = ENTITY.sub('\x01', TAG_FULL.sub('\x00', text))
    return {ch: stripped.count(ch) for ch in '<>&' if stripped.count(ch)}


#: Markup spellings that mean the same thing. Used only for fallback matching,
#: never to rewrite data.
_EQUIVALENT = [
    ('&quot;', '"'), ('&gt;', '>'), ('&lt;', '<'), ('&amp;', '&'),
    ('&ge;', '≥'), ('&le;', '≤'), ('&nbsp;', ' '),
    ('>=', '≥'), ('<=', '≤'), ('<br/>', '<br />'),
]


def match_key(text):
    """A markup-insensitive key for translation-memory lookup.

    Exact matching is tried first everywhere; this is the fallback. It exists
    because the English reference in this repo has had a few unescaped
    characters corrected (raw '>' -> '&gt;', 'Grade >=2' -> 'Grade ≥2'), so its
    strings are no longer byte-identical to upstream's. Without this, a merge
    would treat those already-translated strings as new work.
    """
    key = text
    for entity, literal in _EQUIVALENT:
        key = key.replace(entity, literal)
    return re.sub(r'\s+', ' ', key).strip()


def build_lookup(tm_bucket):
    """Return (exact, normalized) dicts for a translation-memory bucket."""
    exact = dict(tm_bucket)
    norm = {}
    for en, cn in tm_bucket.items():
        norm.setdefault(match_key(en), cn)
    return exact, norm


def lookup(exact, norm, value):
    """Exact match first, then markup-insensitive. Returns (cn, how) or (None, None)."""
    if value in exact:
        return exact[value], 'exact'
    key = match_key(value)
    if key in norm:
        return norm[key], 'normalized'
    return None, None


def needs_translation(value):
    """True when a field value should contain Chinese.

    Short markers such as "CYP2C19: n/a" legitimately have none.
    """
    body = re.sub(r'<[^>]*>', '', value).strip()
    return len(body) > 25
