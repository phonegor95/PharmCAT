#!/usr/bin/env python3
"""Translate a PharmCAT HTML report using local Chinese translation resources."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

HAN = re.compile(r'[\u3400-\u9fff]')
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}
NUMBERS = re.compile(r'\d+(?:\.\d+)?')
DATA_NAMES = ('drugs', 'phenotypes', 'source', 'recommendation',
              'genotype_translation', 'implications')
SKILL = Path(__file__).resolve().parents[1]


def norm(value):
    return re.sub(r'\s+', ' ', html.unescape(value)).strip()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


class Fragment(HTMLParser):
    """Extract text leaves and markup to reject unsafe positional alignment."""
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.leaves = []
        self.events = []
        self.feed(source)

    def handle_data(self, value):
        if norm(value):
            self.leaves.append(norm(value))

    def handle_starttag(self, tag, attrs):
        self.events.append(('start', tag, dict(attrs)))

    def handle_startendtag(self, tag, attrs):
        if tag in VOID:
            self.handle_starttag(tag, attrs)
        else:
            self.events.append(('void', tag, dict(attrs)))

    def handle_endtag(self, tag):
        if tag not in VOID:
            self.events.append(('end', tag))


def load_guidance(repository):
    reporter = repository / 'src/main/resources/org/pharmgkb/pharmcat/reporter'
    references = sorted(reporter.glob('prescribing_guidance.v*.json'))
    if len(references) != 1:
        raise ValueError(f'Expected one paired English guidance reference in {reporter}')
    en = read_json(references[0])
    zh = read_json(reporter / 'prescribing_guidance.json')
    candidates = defaultdict(set)

    def add(source, target):
        if source and target and norm(source) != norm(target):
            candidates[norm(source)].add(norm(target))

    def index(data):
        return {(g['guideline']['id'], r['id']): r
                for g in data['guidelines'] for r in g['recommendations']}

    english, chinese = index(en), index(zh)
    if english.keys() != chinese.keys():
        raise ValueError('English/Chinese guidance recommendation IDs differ')
    for key, er in english.items():
        zr = chinese[key]
        ei, zi = er.get('implications') or [], zr.get('implications') or []
        if len(ei) != len(zi):
            raise ValueError(f'Implication counts differ: {key}')
        for a, b in zip(ei, zi):
            add(a, b)
        add(er.get('population'), zr.get('population'))
        ef = Fragment((er.get('text') or {}).get('html') or '')
        zf = Fragment((zr.get('text') or {}).get('html') or '')
        if len(ef.leaves) == len(zf.leaves) == 1:
            add(ef.leaves[0], zf.leaves[0])
        elif ef.events == zf.events and len(ef.leaves) == len(zf.leaves):
            for a, b in zip(ef.leaves, zf.leaves):
                # Do not align fragments where doses/identifiers cross a tag boundary.
                if Counter(NUMBERS.findall(a)) == Counter(NUMBERS.findall(b)):
                    add(a, b)
    ambiguous = {k for k, v in candidates.items() if len(v) != 1}
    memory = {k: next(iter(v)) for k, v in candidates.items() if k not in ambiguous}
    version = references[0].name[len('prescribing_guidance.v'):-len('.json')]
    return memory, ambiguous, version


class Translator:
    def __init__(self, pharmcat, dictionary_dir, extra):
        self.guidance, self.ambiguous, self.version = load_guidance(pharmcat)
        ui = read_json(SKILL / 'references/report-ui.zh-cn.json')
        self.manual = dict(ui['text'])
        if extra:
            additions = read_json(extra)
            if not isinstance(additions, dict) or not all(
                    isinstance(k, str) and isinstance(v, str) for k, v in additions.items()):
                raise ValueError('--extra must contain an English-to-Chinese string dictionary')
            self.manual.update({norm(k): v for k, v in additions.items()})
        self.attrs = ui['attributes']
        self.lookup = {}
        self.structured = {}
        self.phenotypes = {}
        for name in DATA_NAMES:
            for en, zh in read_json(dictionary_dir / f'{name}.json').items():
                if isinstance(zh, dict):
                    zh = zh['zh-cn']
                self.lookup[norm(en).lower()] = zh
                if name != 'implications':
                    self.structured[norm(en).lower()] = zh
                if name == 'phenotypes':
                    self.phenotypes[en] = zh
        self.labels = {**self.phenotypes, **ui['phrases'],
                       'Deficient with CNSHA': '功能缺陷伴CNSHA',
                       'Deficient': '功能缺陷', 'Normal': '正常'}
        self.phrase = re.compile(r'(?<![A-Za-z])(?:' + '|'.join(
            re.escape(x) for x in sorted(self.labels, key=len, reverse=True)) + r')(?![A-Za-z])')
        self.changed = 0
        self.review = Counter()

    def phrases(self, value):
        return self.phrase.sub(lambda m: self.labels[m[0]], value)

    def text(self, value, stack):
        s = norm(value)
        if not s or any(t in {'style', 'script'} for t, _ in stack):
            return value
        citation = any('citations' in a.get('class', '').split() for _, a in stack)
        if citation:
            if s != 'Citations:':
                return value
            z = '参考文献：'
        elif HAN.search(s):
            return value
        elif s in self.manual:
            z = self.manual[s]
        elif (m := re.fullmatch(r'PharmCAT Report( \[.*\])?', s)):
            z = 'PharmCAT 报告' + (m[1] or '')
        elif (m := re.fullmatch(r'Genotypes called:\s*(\d+)\s*/\s*(\d+)', s)):
            z = f'已判定基因型：{m[1]} / {m[2]}'
        elif s.lower() in self.structured:
            z = self.structured[s.lower()]
        elif s in self.guidance:
            z = self.guidance[s]
        elif s in self.ambiguous:
            # A shared English fragment can have context-specific Chinese translations.
            self.review[s] += 1
            return value
        elif s.lower() in self.lookup:
            z = self.lookup[s.lower()]
        elif ' / ' in s and all(p.lower() in self.lookup for p in s.split(' / ')):
            z = ' / '.join(self.lookup[p.lower()] for p in s.split(' / '))
        elif (m := re.fullmatch(r'(.+) allele match data', s)):
            z = m[1] + ' 等位基因匹配数据'
        elif (m := re.fullmatch(
                r'The (.+) allele assignment is characterized by the absence of variants '
                r'at the positions that are included in the underlying allele definitions\.', s)):
            z = self.phrases(m[1]) + ' 等位基因的判定依据为：在相应等位基因定义所包含的位点未发现变异。'
        elif ' - ' in s:
            left, right = s.rsplit(' - ', 1)
            z = left + ' - ' + self.phrases(right)
        else:
            z = self.phrases(s)
            if '（活性评分：' in z:
                z = z.replace(')', '）')
        # Date handling uses a real parser rather than hard-coded patient metadata.
        if z == s and re.fullmatch(r'[A-Z][a-z]+ \d{1,2}, \d{4}', s):
            try:
                date = datetime.strptime(s, '%B %d, %Y')
                z = f'{date.year}年{date.month}月{date.day}日'
            except ValueError:
                pass
        if z == s:
            if re.search(r'[A-Za-z]{3,}', s):
                self.review[s] += 1
            return value
        self.changed += 1
        # Track partly untranslated prose too; variant names before " - " are identifiers.
        body = z.rsplit(' - ', 1)[-1]
        if re.search(r'(?i)\b(?:metabolizer|alleles?|function|the|with|and|not|for)\b', body):
            self.review[z] += 1
        return re.match(r'\s*', value)[0] + html.escape(z, quote=False) + re.search(r'\s*$', value)[0]


class Report(HTMLParser):
    def __init__(self, source, translator):
        super().__init__(convert_charrefs=False)
        self.stack, self.edits = [], []
        self.translator = translator
        self.lines = [0] + [m.end() for m in re.finditer('\n', source)]
        self.feed(source)
        self.close()

    def source_offset(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, dict(attrs)))
        old = self.get_starttag_text()
        new = old
        if tag == 'html':
            lang = re.compile(r'\blang\s*=\s*([\'"])[^\'"]*\1', re.I)
            new = lang.sub('lang="zh-CN"', new) if lang.search(new) else new[:-1] + ' lang="zh-CN">'
        # Translate only human-facing alt/title/ARIA text, retaining every other attribute.
        for key, val in attrs:
            if key in {'alt', 'title', 'aria-label'} and val in self.translator.attrs:
                pattern = re.compile(r'(\b' + re.escape(key) + r'\s*=\s*)([\'"])(.*?)\2', re.I | re.S)
                new = pattern.sub(lambda m: m[1] + m[2] + html.escape(
                    self.translator.attrs[val], quote=True) + m[2], new)
        if new != old:
            start = self.source_offset()
            self.edits.append((start, start + len(old), new))

    def handle_startendtag(self, tag, attrs):
        previous = len(self.stack)
        self.handle_starttag(tag, attrs)
        del self.stack[previous:]

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack = self.stack[:i]
                break

    def handle_data(self, value):
        translated = self.translator.text(value, self.stack)
        if translated != value:
            start = self.source_offset()
            self.edits.append((start, start + len(value), translated))


class Audit(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.events, self.texts = [], []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.events.append(('start', tag, dict(attrs)))

    def handle_startendtag(self, tag, attrs):
        self.events.append(('void', tag, dict(attrs)))

    def handle_endtag(self, tag):
        self.events.append(('end', tag))

    def handle_data(self, value):
        self.texts.append(value)


def validate(source, result, translator):
    a, b = Audit(source), Audit(result)
    if len(a.events) != len(b.events) or len(a.texts) != len(b.texts):
        raise ValueError('HTML structure or text-node boundaries changed')
    for old, new in zip(a.events, b.events):
        if old[:2] != new[:2]:
            raise ValueError('HTML tag structure changed')
        if len(old) == 3:
            attrs = dict(old[2])
            if old[1] == 'html':
                attrs['lang'] = 'zh-CN'
            for key in ('alt', 'title', 'aria-label'):
                if attrs.get(key) in translator.attrs:
                    attrs[key] = translator.attrs[attrs[key]]
            if attrs != new[2]:
                raise ValueError(f'Functional attributes changed: {old[1]}')
    for old, new in zip(a.texts, b.texts):
        if old == new:
            continue
        if HAN.search(old):
            raise ValueError('Existing Chinese text changed')
        if Counter(NUMBERS.findall(old)) != Counter(NUMBERS.findall(new)):
            try:
                date = datetime.strptime(norm(old), '%B %d, %Y')
            except ValueError:
                raise ValueError(f'Numbers changed: {norm(old)[:160]}') from None
            if norm(new) != f'{date.year}年{date.month}月{date.day}日':
                raise ValueError('Date changed')
    return {'html_events': len(a.events), 'text_nodes': len(a.texts),
            'numeric_values': 'preserved', 'existing_chinese': 'preserved'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--pharmcat', type=Path, help='PharmCAT checkout (auto-detected from skill location)')
    parser.add_argument('--dictionaries', type=Path, help='GenDecoder assets/pharmcat/data/zh-cn directory')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--extra', type=Path, help='Additional exact English-to-Chinese JSON mapping')
    args = parser.parse_args()
    pharmcat = args.pharmcat
    if pharmcat is None:
        pharmcat = next((p for p in SKILL.parents if (p / 'README_Chinese.md').is_file()), None)
    if pharmcat is None:
        parser.error('Use --pharmcat to select the PharmCAT checkout')
    dictionaries = args.dictionaries or pharmcat.parent / 'GenDecoder/assets/pharmcat/data/zh-cn'
    output = args.output or args.input.with_name(args.input.stem + '.zh-cn.html')
    review_path = output.with_suffix('.translation-review.json')
    if args.input.resolve() in {output.resolve(), review_path.resolve()}:
        parser.error('Output must differ from input')
    if output.exists() or review_path.exists():
        parser.error('Output/review file already exists; choose a new --output')
    raw = args.input.read_bytes()
    source = raw.decode('utf-8')
    translator = Translator(pharmcat, dictionaries, args.extra)
    match = re.search(r'<th>PharmCAT Version</th>\s*<td>([^<]+)</td>', source)
    if match and not re.match(re.escape(translator.version) + r'(?:-|$)', match[1]):
        raise ValueError(f'Report version {match[1]} does not match guidance {translator.version}')
    report = Report(source, translator)
    result = source
    for start, end, replacement in reversed(report.edits):
        result = result[:start] + replacement + result[end:]
    checks = validate(source, result, translator)
    if raw != args.input.read_bytes():
        raise ValueError('Input changed while translating')
    audit = {'input_sha256': hashlib.sha256(raw).hexdigest(),
             'output': str(output), 'guidance_version': translator.version,
             'changed_nodes': translator.changed, 'validation': checks,
             'review_note': 'Review remaining English; technical identifiers and proper names can remain.',
             'remaining_english': dict(translator.review)}
    # Validate fully in memory before creating a deliverable. Never overwrite existing reports.
    with output.open('x', encoding='utf-8', newline='') as fh:
        fh.write(result)
    with review_path.open('x', encoding='utf-8') as fh:
        json.dump(audit, fh, ensure_ascii=False, indent=2)
        fh.write('\n')
    print(json.dumps({'output': str(output), 'review': str(review_path),
                      'changed_nodes': translator.changed, 'validation': checks}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        print(f'Error: {error}', file=sys.stderr)
        sys.exit(1)
