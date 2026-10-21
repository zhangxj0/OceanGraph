"""Run a bounded practical multi-hop job with shared model routes and durable accounting."""
import argparse
import concurrent.futures
try:
    import fcntl
except ImportError:  # Offline configuration checks are also useful on Windows.
    fcntl = None
import json
import os
import random
import re
import signal
import sys
import threading
import time
from collections import Counter
from pathlib import Path

import requests
from .state import (State, BudgetStop, arithmetic_violations, supervise, check_run_allowed,
                        start_watchdog, single_target_violations, source_relevance_violations)
from .prompts import generation_prompt, verification_prompt
from .config import load_routes, request_for, route_summary

DOMAIN = 'Ocean Science and Marine Biogeochemistry'
DEFAULT_OUTPUT = Path('output/practical_batch')
LIMITS = {'requests': 40000, 'input_tokens': 200000000, 'output_tokens': 50000000,
          'seconds': 86400, 'max_tokens_per_request': 8192}
TOPIC_DOMAIN = {'carbon_pump_flux': 'carbon_biogeochemistry', 'acidification_carbonate': 'carbon_biogeochemistry',
                'nutrients_microbes': 'carbon_biogeochemistry', 'coastal_blue_carbon': 'carbon_biogeochemistry',
                'physical_climate': 'physical_ocean_climate', 'ecology_plankton': 'marine_ecology_fisheries',
                'observing_models': 'remote_sensing_observing', 'sediment_paleo': 'physical_ocean_climate'}


def atomic_json(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


def extract_json(text):
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text)
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError('Response must be a JSON object')
    return value


class Client:
    def __init__(self, state, routes, stop, deadline=float('inf')):
        self.state, self.routes, self.stop = state, routes, stop
        self.provenance = route_summary(routes)
        self.deadline = deadline
        self.cooldown_lock = threading.Lock()
        self.cooldown_until = 0
        self.fatal_reason = None

    def call(self, prompt, stage, source):
        for attempt in range(2):
            if self.stop.is_set() or time.monotonic() >= self.deadline:
                raise BudgetStop('Job stopping')
            delay = max(0, self.cooldown_until - time.monotonic())
            if self.stop.wait(delay):
                raise BudgetStop('Job stopping')
            if time.monotonic() >= self.deadline:
                raise BudgetStop('Absolute runtime deadline reached')
            url, headers, payload, route = request_for(self.routes, stage, prompt, LIMITS['max_tokens_per_request'])
            call_id = self.state.reserve(stage, source, len(json.dumps(payload, ensure_ascii=False).encode('utf-8')) + 512, payload['max_tokens'], route=route)
            status, data, finish, content, usage = None, None, None, '', None
            retryable, error = False, None
            try:
                response = requests.post(url, json=payload, headers=headers,
                    timeout=(20, route['timeout']), allow_redirects=False)
                status = response.status_code
                if status == 200:
                    data = response.json()
                    usage = data.get('usage')
                    choice = (data.get('choices') or [{}])[0]
                    finish = choice.get('finish_reason')
                    content = (choice.get('message') or {}).get('content') or ''
                    if finish == 'length':
                        error = 'Output truncated; candidate source skipped without same-parameter retry'
                    elif not content:
                        error = 'Empty model content'
                elif status in (401, 403):
                    self.fatal_reason = 'Model endpoint returned HTTP ' + str(status)
                    self.stop.set()
                    error = self.fatal_reason
                elif status in (408, 429, 500, 502, 503, 504):
                    retryable = True
                    error = 'Retryable HTTP ' + str(status)
                    if status == 429:
                        with self.cooldown_lock:
                            self.cooldown_until = max(self.cooldown_until, time.monotonic() + 30)
                else:
                    error = 'Model endpoint returned HTTP ' + str(status)
            except (requests.RequestException, ValueError) as exc:
                error = type(exc).__name__
                retryable = isinstance(exc, requests.RequestException)
            finally:
                # No key, headers or hidden reasoning is persisted.
                self.state.finish(call_id, status, usage, content, finish)
            if not error:
                return extract_json(content)
            if retryable and attempt == 0 and not self.stop.wait(5 + random.random() * 5):
                continue
            raise RuntimeError(error)
        raise RuntimeError('Request attempts exhausted')


def process_source(source, client, state, atomic_qa_violations):
    relevance_problems = source_relevance_violations(source)
    if relevance_problems:
        state.reject(source['id'], 'source:' + ','.join(relevance_problems), {'title': source['title']})
        return 0
    body = '\n\n'.join(source['chunks'])
    prompt = generation_prompt(source['title'], body)
    if source.get('avoid_questions'):
        prompt += '\nThese questions already exist for this source. Generate DIFFERENT linked questions, not paraphrases: ' + json.dumps(source['avoid_questions'], ensure_ascii=False)
    response = client.call(prompt, 'generation', source['id'])
    pairs = response.get('qa_pairs', [])
    candidates = []
    for index, raw in enumerate(pairs[:4] if isinstance(pairs, list) else []):
        if not isinstance(raw, dict):
            continue
        pair = dict(raw)
        pair['candidate_id'] = f'q{index + 1}'
        pair['question'] = ' '.join(str(pair.get('question', '')).split())
        pair['answer'] = ' '.join(str(pair.get('answer', '')).split())
        pair['short_answers'] = [pair['answer']]
        problems = atomic_qa_violations(pair['question'], pair['answer'], pair['short_answers'])
        problems += single_target_violations(pair['question'])
        problems += arithmetic_violations(pair, body)
        if pair.get('question_type') not in ('bridge', 'comparison', 'causal', 'temporal', 'spatial', 'numeric_aggregation'):
            problems.append('invalid_question_type')
        if pair.get('answer_type') not in ('entity', 'numeric', 'date', 'yes_no', 'short_text'):
            problems.append('invalid_answer_type')
        if problems:
            state.reject(source['id'], 'local:' + ','.join(problems), pair)
        else:
            candidates.append(pair)
    if not candidates:
        return 0
    reply = client.call(verification_prompt(source['title'], body, json.dumps(candidates, ensure_ascii=False)),
                        'verification', source['id'])
    reviews = reply.get('reviews', [])
    review_ids = [r.get('candidate_id') for r in reviews if isinstance(r, dict)] if isinstance(reviews, list) else []
    if len(review_ids) != len(set(review_ids)):
        raise ValueError('Duplicate verifier ids')
    by_id = {r['candidate_id']: r for r in reviews if isinstance(r, dict) and 'candidate_id' in r}
    accepted = 0
    checks = ('question_standalone', 'single_target', 'answer_supported', 'domain_relevant',
              'multihop_plausible', 'arithmetic_consistent', 'conditions_consistent')
    for pair in candidates:
        review = by_id.get(pair['candidate_id'], {})
        passed = (review.get('verdict') == 'ACCEPT' and all(review.get(k) is True for k in checks)
                  and review.get('quality') in ('clear_multi_step', 'shallow_linkage'))
        if not passed:
            state.reject(source['id'], 'verification', {'qa': pair, 'review': review})
            continue
        decision = {k: review[k] for k in checks}
        decision.update(passes=True, basic_checks_passed=True, verdict='ACCEPT', status='MULTIHOP_PLAUSIBLE',
                        verification_profile='practical_multihop', verification_mode='qualitative',
                        necessity_verified=False, verification_api_calls=1, reason=review.get('reason', ''))
        record = {**pair, 'domain': DOMAIN, 'subdomain': pair.get('subdomain') or TOPIC_DOMAIN[source['topic']],
                  'taxonomy_version': '3.0.0', 'selection_status': 'LOCAL_SELECTED',
                  'verification_profile': 'practical_multihop', 'multihop_necessity_result': decision,
                  'quality_label': review['quality'], 'review': review,
                  'sample_topic': source['topic'], 'source_title': source['title'],
                  'source_url': source['source_url'], 'source_doi': source['doi'],
                  'model_provenance': client.provenance}
        if state.accept(source['id'], record):
            accepted += 1
        else:
            state.reject(source['id'], 'duplicate_or_quota', pair)
    return accepted


def export_dataset(state, output, final, training, partial=False):
    from oceangraph.training import export_training_dataset, to_training_record
    records, sources = state.snapshot()
    compact, expanded, corpus, used = [], [], [], set()
    source_chunks = {}
    for seq, sid, item in records:
        source = sources[sid]
        if sid not in source_chunks:
            source_chunks[sid] = [{'file_name': sid, 'chunk_id': f'p{i:02d}', 'content': text,
                                    'artifact': [], 'image_path': None} for i, text in enumerate(source['chunks'], 1)]
        row = to_training_record(item, split='sample', source_documents=[sid])
        row.update(sample_id=f'ocean20k_{seq:06d}', sample_topic=item['sample_topic'],
                   source_title=item['source_title'], source_url=item['source_url'], quality_label=item['quality_label'],
                   model_provenance=item.get('model_provenance', {'status': 'legacy_unrecorded'}))
        compact.append(row)
        if training:
            expanded.append({**item, 'context_chunks': source_chunks[sid]})
        if sid not in used:
            corpus.extend(source_chunks[sid])
            used.add(sid)
    basename = 'qa_partial.jsonl' if partial else 'qa_20000.jsonl'
    path = output / basename
    temp = path.with_suffix('.tmp')
    with temp.open('w', encoding='utf-8') as f:
        for row in compact:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
    temp.replace(path)
    if training:
        manifest = export_training_dataset(expanded, corpus, output / 'training', split_seed=20261019)
        if manifest['exported_records'] != len(records) or manifest['source_leakage_detected']:
            raise RuntimeError('Training export rejected records or leaked source ids')
        search_dir = output / 'search_r1'
        search_dir.mkdir(exist_ok=True)
        prefix = ('Answer the given question. Conduct reasoning inside <think> and </think>. '
                  'If more information is needed, use <search> query </search>; results appear '
                  'inside <information> and </information>. You may search multiple times. '
                  'Give only the final answer inside <answer> and </answer>. Question: ')
        for split in ('train', 'dev', 'test'):
            with (search_dir / f'{split}.jsonl').open('w', encoding='utf-8') as handle:
                for index, line in enumerate((output / 'training' / f'{split}.jsonl').read_text(encoding='utf-8').splitlines()):
                    qa = json.loads(line)
                    value = {'data_source': 'oceangraph_practical20k', 'prompt': [{'role': 'user', 'content': prefix + qa['question']}],
                             'ability': 'fact-reasoning', 'reward_model': {'style': 'rule', 'ground_truth': {'target': qa['short_answers']}},
                             'extra_info': {'split': split, 'index': index, 'qa_id': qa['qa_id'],
                                            'source_documents': qa['metadata']['source_documents']}}
                    handle.write(json.dumps(value, ensure_ascii=False) + '\n')
    summary = {'accepted': len(records), 'target': state.target, 'source_documents': len(used),
               'topics': dict(Counter(r['sample_topic'] for r in compact)),
               'question_types': dict(Counter(r['question_type'] for r in compact)),
               'quality_labels': dict(Counter(r['quality_label'] for r in compact)),
               'api_usage': state.totals(), 'completed': final and len(records) == state.target,
               'verification_scope': 'Configured model qualitative review, source-backed arithmetic, exact deduplication and within-source near-duplicate check; no proof of per-hop necessity. Per-record provenance is in qa_*.jsonl; older records may be legacy_unrecorded.'}
    atomic_json(output / 'dataset_summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--target', type=int, default=20000)
    parser.add_argument('--llm-config', type=Path, default=None)
    parser.add_argument('--check-config', action='store_true', help='Validate routes and environment keys without API calls or run writes')
    parser.add_argument('--exclude', type=Path, help='Optional JSON with questions to exclude')
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--max-documents', type=int, default=0)
    parser.add_argument('--export-only', action='store_true')
    args = parser.parse_args()
    if args.target <= 0 or args.max_documents < 0:
        parser.error('target must be positive and max-documents nonnegative')
    config_path = args.llm_config or Path(os.environ.get('OCEANGRAPH_LLM_CONFIG') or 'configs/llm.yaml')
    routes = None if args.export_only else load_routes(config_path, require_keys=True)
    if args.check_config:
        if routes is None:
            parser.error('--check-config and --export-only cannot be combined')
        print(json.dumps(route_summary(routes), ensure_ascii=False, indent=2))
        return
    if fcntl is None:
        parser.error('Batch execution requires Linux/macOS file locks; --check-config works on Windows')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    lockfile = (output / 'worker.lock').open('w')
    try:
        fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('Another worker owns this run')
    from oceangraph.verification.quality import atomic_qa_violations
    state = State(output / 'run.sqlite', target=args.target)
    (output / 'worker.pid').write_text(str(os.getpid()))
    removed = state.revalidate_samples()
    if removed:
        print(json.dumps({'pilot_recheck_removed': removed}), flush=True)
    if args.export_only:
        print(json.dumps(export_dataset(state, output, state.totals()['accepted'] == state.target, True), ensure_ascii=False))
        return
    if state.totals()['accepted'] >= state.target:
        raise SystemExit('Target already reached; use --export-only if needed')
    prior_active = float(state.meta('active_seconds') or 0)
    check_run_allowed((output / 'STOP').exists() or (output / 'runtime_limit_reached').exists(), prior_active, LIMITS['seconds'])
    state.load_inventory(output / 'sources.jsonl')
    if args.exclude:
        excluded = json.loads(args.exclude.read_text(encoding='utf-8'))
        state.exclude_questions(excluded.get('questions', []))
    state.recover()
    stop = threading.Event()
    remaining_runtime = LIMITS['seconds'] - prior_active
    deadline = time.monotonic() + remaining_runtime
    client = Client(state, routes, stop, deadline=deadline)
    def hard_timeout():
        stop.set()
        try:
            (output / 'runtime_limit_reached').write_text('Absolute runtime watchdog terminated the worker. Unsettled request reservations remain charged.')
        finally:
            os._exit(124)
    watchdog = start_watchdog(remaining_runtime, hard_timeout)
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    config = {'target': state.target, 'workers': max(1, min(8, args.workers)), 'limits': LIMITS,
              'models': client.provenance, 'llm_config': str(config_path.resolve()),
              'max_per_document': 4, 'numeric_aggregation_max_fraction': 0.35,
              'version': '4.0.0', 'pid': os.getpid()}
    atomic_json(output / 'run_config.json', config)
    history = output / 'config_history'
    history.mkdir(exist_ok=True)
    atomic_json(history / (time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '_' + str(os.getpid()) + '.json'), config)
    claim_lock = threading.Lock()
    claimed = 0
    errors = []
    state.meta('status', 'running')
    start = time.monotonic()
    initial_accepted = state.totals()['accepted']

    def worker():
        nonlocal claimed
        consecutive_errors = 0
        while not stop.is_set() and state.totals()['accepted'] < state.target:
            with claim_lock:
                if args.max_documents and claimed >= args.max_documents:
                    return
                source = state.claim()
                if source is None:
                    return
                claimed += 1
            try:
                count = process_source(source, client, state, atomic_qa_violations)
                state.mark_source(source['id'], 'done')
                consecutive_errors = 0
                print(json.dumps({'source': source['id'], 'accepted': count,
                                  'total': state.totals()['accepted']}, ensure_ascii=False), flush=True)
            except BudgetStop as exc:
                state.mark_source(source['id'], 'pending', str(exc))
                errors.append(str(exc))
                stop.set()
            except Exception as exc:
                error = type(exc).__name__ + ': ' + str(exc)
                for profile in routes.values():
                    if profile.api_key:
                        error = error.replace(profile.api_key, '[REDACTED]')
                error = error[:400]
                state.mark_source(source['id'], 'failed', error)
                errors.append(error)
                consecutive_errors += 1
                print(json.dumps({'source': source['id'], 'error': error}), flush=True)
                if consecutive_errors >= 6:
                    client.fatal_reason = 'Repeated per-worker source errors'
                    stop.set()

    last_export = initial_accepted
    def tick():
        nonlocal last_export
        elapsed = prior_active + time.monotonic() - start
        if elapsed >= LIMITS['seconds']:
            client.fatal_reason = 'Active runtime limit reached'
            stop.set()
        if (output / 'STOP').exists():
            client.fatal_reason = 'STOP file requested'
            stop.set()
        totals = state.totals()
        state.meta('active_seconds', elapsed)
        atomic_json(output / 'progress.json', {'status': 'stopping' if stop.is_set() else 'running',
            'target': state.target, 'accepted': totals['accepted'], 'sources': state.source_counts(),
            'usage': totals, 'pid': os.getpid(), 'active_seconds': round(elapsed, 2),
            'updated_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'recent_errors': errors[-5:]})
        if totals['accepted'] - last_export >= 500:
            export_dataset(state, output, False, False, partial=True)
            last_export = totals['accepted']

    while True:
        with concurrent.futures.ThreadPoolExecutor(max_workers=config['workers']) as pool:
            futures = [pool.submit(worker) for _ in range(config['workers'])]
            supervise(futures, stop, tick)
            for future in futures:
                future.result()
        if stop.is_set() or args.max_documents or state.totals()['accepted'] >= state.target:
            break
        queued = state.queue_second_pass()
        if queued == 0:
            break
        print(json.dumps({'additional_source_pass_queued': queued}), flush=True)
    elapsed = prior_active + time.monotonic() - start
    state.meta('active_seconds', elapsed)
    accepted = state.totals()['accepted']
    status = ('completed' if accepted == state.target else 'stopped' if stop.is_set()
              else 'pilot_complete' if args.max_documents else 'sources_exhausted')
    state.meta('status', 'finalizing' if status == 'completed' else status)
    summary = export_dataset(state, output, status == 'completed', status == 'completed', partial=status != 'completed')
    if status == 'pilot_complete':
        export_dataset(state, output, False, True, partial=True)
    atomic_json(output / 'progress.json', {'status': status, 'target': state.target, 'accepted': accepted,
        'sources': state.source_counts(), 'usage': state.totals(), 'pid': os.getpid(),
        'active_seconds': round(elapsed, 2), 'stop_reason': client.fatal_reason or (errors[-1] if stop.is_set() and errors else None),
        'updated_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
    state.meta('status', status)
    watchdog.cancel()
    print('RUN_SUMMARY ' + json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
