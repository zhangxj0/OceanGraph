"""Select diverse, deduplicated scientific body text locally; no API calls."""
import argparse
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from .sources import TOPICS, MARINE, field, source_context


def publish_inventory(path, rows):
    """An interrupted preparation must never publish a partial source list."""
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', encoding='utf-8') as handle:
        for source in rows:
            handle.write(json.dumps(source, ensure_ascii=False) + '\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--pattern', default='*.md')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--exclude', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if any((args.output/name).exists() for name in ('sources.jsonl', 'run.sqlite')):
        raise SystemExit('Output already contains an inventory or run; use a new directory')
    if not args.input.is_dir():
        raise SystemExit('Input directory does not exist')
    excluded = json.loads(args.exclude.read_text(encoding='utf-8')) if args.exclude else {}
    excluded_docs = set(excluded.get('source_documents', []))
    paths = sorted(args.input.glob(args.pattern))
    if not paths:
        raise SystemExit('No source files matched --pattern')
    random.Random(20261019).shuffle(paths)
    seen_titles, seen_dois, seen_content = set(), set(), set()
    pools, counts = defaultdict(list), Counter()
    for path in paths:
        counts['scanned'] += 1
        if path.relative_to(args.input).with_suffix('').as_posix() in excluded_docs:
            counts['previous_sample_sources_excluded'] += 1
            continue
        raw = path.read_text(encoding='utf-8', errors='replace')
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', raw, re.S)
        if not match:
            counts['missing_metadata'] += 1
            continue
        header, body = match.group(1), raw[match.end():]
        title = field(header, 'title')
        if re.search(r'patient|clinical|cancer|dinosaur|lung|breast|dental|freshwater lake|agricultural soil', title, re.I):
            counts['off_topic_title'] += 1
            continue
        marine_count = len(MARINE.findall(title * 3 + body[:5000]))
        if marine_count < 3 or len(body) < 4500:
            counts['insufficient_marine_body'] += 1
            continue
        body = re.sub(r'\[\[.*?\]\]', '', body)
        chunks = source_context(body)
        if len(chunks) < 2 or sum(map(len, chunks)) < 3500:
            counts['short_context'] += 1
            continue
        normalized_title = re.sub(r'\W+', '', title.casefold())
        doi = field(header, 'doi_or_report_id') or field(header, 'doi')
        doi = re.sub(r'^https?://(?:dx\.)?doi.org/', '', doi, flags=re.I).strip().casefold()
        digest = hashlib.sha256('\n'.join(chunks).encode()).hexdigest()
        if normalized_title in seen_titles or (doi and doi in seen_dois) or digest in seen_content:
            counts['duplicate_document'] += 1
            continue
        text = title * 3 + body[:5000]
        scores = {topic: len(re.findall(pattern, text, re.I)) for topic, pattern in TOPICS.items()}
        topic = max(scores, key=scores.get)
        if scores[topic] == 0:
            counts['no_scientific_topic'] += 1
            continue
        seen_titles.add(normalized_title)
        if doi:
            seen_dois.add(doi)
        seen_content.add(digest)
        pools[topic].append({'id': path.relative_to(args.input).with_suffix('').as_posix(), 'file': path.name, 'title': title,
                            'source_url': field(header, 'source_url'), 'doi': doi,
                            'topic': topic, 'chunks': chunks, 'body_sha256': hashlib.sha256(body.encode()).hexdigest()})
        counts['eligible'] += 1
        if counts['scanned'] % 2000 == 0:
            print(json.dumps({'scanned': counts['scanned'], 'eligible': counts['eligible']}), flush=True)
    order = []
    while any(pools.values()):
        for topic in TOPICS:
            if pools[topic]:
                order.append(pools[topic].pop())
    publish_inventory(args.output / 'sources.jsonl', order)
    summary = {'counts': dict(counts), 'topics': dict(Counter(s['topic'] for s in order)),
               'maximum_acceptance_at_4_per_document': len(order) * 4,
               'seed': 20261019, 'excluded_documents': len(excluded_docs)}
    (args.output / 'source_inventory.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
