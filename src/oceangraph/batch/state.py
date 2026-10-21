"""Durable, bounded state and deterministic arithmetic checks; no network imports."""
import difflib
import hashlib
import json
import re
import sqlite3
import threading
import time
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


class BudgetStop(RuntimeError):
    pass


def supervise(futures, stop, tick, interval=5):
    """Stop request workers before a failing supervisor enters executor shutdown."""
    try:
        while not all(f.done() for f in futures):
            tick()
            time.sleep(interval)
    except BaseException:
        stop.set()
        raise


def check_run_allowed(stop_requested, active_seconds, runtime_limit):
    if stop_requested:
        raise BudgetStop('STOP requested before launch')
    if active_seconds >= runtime_limit:
        raise BudgetStop('Active runtime limit already exhausted')


def start_watchdog(seconds, callback):
    timer = threading.Timer(max(0, seconds), callback)
    timer.daemon = True
    timer.start()
    return timer


def normalized(text):
    return re.sub(r'\W+', '', unicodedata.normalize('NFKC', str(text)).casefold())


def numbers(text):
    text = str(text).replace('−', '-').replace('–', '-')
    text = re.sub(r'(?<=\d),(?=\d{3}(?:\D|$))', '', text)
    return [Decimal(s) for s in re.findall(r'(?<!\w)[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?', text)]


def single_target_violations(question):
    if re.search(r'\b(?:and|or)\s+(?:(?:by|for|at|in|with|from|to)\s+)?(?:who|what|which|where|when|why|how)\b', question, re.I):
        return ['compound_interrogative']
    if re.search(r'\b(?:what|which)\s+(?:[a-z-]+\s+){0,4}(?:temperature\s+and\s+(?:time|duration)|time\s+and\s+temperature)\b', question, re.I):
        return ['multiple_requested_attributes']
    return []


def source_relevance_violations(source):
    title = source.get('title', '')
    abstract = '\n'.join(source.get('chunks', []))[:3000]
    if re.search(r'\b(?:dental|caries|periodontal|gingivitis|orthodont\w*|oral health|oral hygiene)\b', title + ' ' + abstract, re.I):
        # A fishing occupation or coastal location does not make dentistry marine science.
        return ['off_domain_human_dentistry']
    return []


def arithmetic_violations(qa, context):
    if qa.get('question_type') != 'numeric_aggregation':
        return []
    calc = qa.get('calculation')
    if not isinstance(calc, dict):
        return ['missing_calculation']
    problems, values = [], []
    try:
        operands = calc['operands']
        if not isinstance(operands, list) or len(operands) != 2:
            return ['expected_two_operands']
        for operand in operands:
            value = Decimal(str(operand['value']))
            if not value.is_finite():
                return ['nonfinite_operand']
            quote = str(operand['source_quote'])
            if len(normalized(quote)) < 12 or normalized(quote) not in normalized(context):
                problems.append('quote_not_in_source')
            if value not in numbers(quote):
                problems.append('operand_not_in_quote')
            values.append(value)
        if all(v in numbers(qa['question']) for v in values):
            problems.append('all_operands_in_question')
        a, b = values
        operation = calc['operation']
        if operation == 'difference':
            result = a - b
        elif operation == 'absolute_difference':
            result = abs(a - b)
        elif operation == 'ratio':
            result = a / b
        elif operation == 'percentage_reduction':
            result = (a - b) / a * 100
        elif operation == 'percentage_change':
            result = (b - a) / a * 100
        elif operation == 'sum':
            result = a + b
        elif operation == 'product':
            result = a * b
        else:
            return problems + ['unsupported_operation']
        decimals = int(calc.get('decimals', 2))
        if not 0 <= decimals <= 6:
            return problems + ['unsupported_precision']
        result = result.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)
        answer_numbers = numbers(qa.get('answer', ''))
        if not answer_numbers or answer_numbers[0] != result:
            problems.append('arithmetic_answer_mismatch')
    except (KeyError, TypeError, ValueError, InvalidOperation, ZeroDivisionError):
        problems.append('malformed_calculation')
    return list(dict.fromkeys(problems))


class State:
    def __init__(self, path, target=20000, max_requests=40000, max_input=200000000,
                 max_output=50000000, numeric_fraction=0.35):
        self.lock = threading.RLock()
        self.target = target
        self.max_requests, self.max_input, self.max_output = max_requests, max_input, max_output
        self.numeric_limit = int(target * numeric_fraction)
        self.db = sqlite3.connect(str(path), check_same_thread=False, timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS counters(key TEXT PRIMARY KEY,value INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY,topic TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',data TEXT NOT NULL,error TEXT);
        CREATE TABLE IF NOT EXISTS calls(id INTEGER PRIMARY KEY AUTOINCREMENT,stage TEXT,source TEXT,input_reserved INTEGER,output_reserved INTEGER,input_actual INTEGER,output_actual INTEGER,status INTEGER,finish_reason TEXT,response TEXT,created REAL,finished REAL);
        CREATE TABLE IF NOT EXISTS call_routes(call_id INTEGER PRIMARY KEY, metadata TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS samples(seq INTEGER PRIMARY KEY AUTOINCREMENT,source TEXT,question_key TEXT UNIQUE,qa_id TEXT UNIQUE,data TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS samples_source ON samples(source);
        CREATE INDEX IF NOT EXISTS source_status ON sources(status);
        CREATE TABLE IF NOT EXISTS rejects(id INTEGER PRIMARY KEY AUTOINCREMENT,source TEXT,reason TEXT,data TEXT);
        CREATE TABLE IF NOT EXISTS excluded_questions(question_key TEXT PRIMARY KEY);
        ''')
        with self.db:
            for key in ('requests', 'input_accounted', 'output_accounted', 'input_reported', 'output_reported', 'accepted', 'numeric'):
                self.db.execute('INSERT OR IGNORE INTO counters VALUES (?,0)', (key,))
            old = self.db.execute("SELECT value FROM meta WHERE key='target'").fetchone()
            if old and int(old[0]) != target:
                raise ValueError('Cannot change the target for an existing run')
            self.db.execute("INSERT OR IGNORE INTO meta VALUES ('target',?)", (str(target),))
            self.db.execute("INSERT OR IGNORE INTO meta VALUES ('created',?)", (str(time.time()),))

    def close(self):
        with self.lock:
            self.db.close()

    def _increment(self, key, amount):
        self.db.execute('UPDATE counters SET value=value+? WHERE key=?', (amount, key))

    def totals(self):
        with self.lock:
            return {r['key']: r['value'] for r in self.db.execute('SELECT * FROM counters')}

    def reserve(self, stage, source, input_tokens, output_tokens, route=None):
        with self.lock, self.db:
            totals = self.totals()
            if (totals['requests'] >= self.max_requests or
                    totals['input_accounted'] + input_tokens > self.max_input or
                    totals['output_accounted'] + output_tokens > self.max_output):
                raise BudgetStop('Request/input/output limit reached')
            cursor = self.db.execute('INSERT INTO calls(stage,source,input_reserved,output_reserved,created) VALUES (?,?,?,?,?)',
                                     (stage, source, input_tokens, output_tokens, time.time()))
            for key, value in (('requests', 1), ('input_accounted', input_tokens), ('output_accounted', output_tokens)):
                self._increment(key, value)
            if route is not None:
                self.db.execute('INSERT INTO call_routes VALUES (?,?)', (cursor.lastrowid, json.dumps(route, sort_keys=True)))
            return cursor.lastrowid

    def finish(self, call_id, status, usage, response, finish_reason):
        with self.lock, self.db:
            call = self.db.execute('SELECT * FROM calls WHERE id=?', (call_id,)).fetchone()
            if call['finished'] is not None:
                raise ValueError('Call has already been settled')
            actual_in = usage.get('prompt_tokens') if isinstance(usage, dict) else None
            actual_out = usage.get('completion_tokens') if isinstance(usage, dict) else None
            known = (isinstance(actual_in, int) and not isinstance(actual_in, bool) and actual_in >= 0 and
                     isinstance(actual_out, int) and not isinstance(actual_out, bool) and actual_out >= 0)
            if known:
                self._increment('input_accounted', actual_in - call['input_reserved'])
                self._increment('output_accounted', actual_out - call['output_reserved'])
                self._increment('input_reported', actual_in)
                self._increment('output_reported', actual_out)
            self.db.execute('UPDATE calls SET status=?,input_actual=?,output_actual=?,response=?,finish_reason=?,finished=? WHERE id=?',
                            (status, actual_in if known else None, actual_out if known else None,
                             response, finish_reason, time.time(), call_id))

    def add_sources(self, rows):
        with self.lock, self.db:
            self.db.executemany('INSERT OR IGNORE INTO sources(id,topic,data) VALUES (?,?,?)',
                                [(r['id'], r['topic'], json.dumps(r, ensure_ascii=False)) for r in rows])

    def load_inventory(self, path):
        if self.meta('sources_import_complete') == 'true':
            return
        batch = []
        with path.open(encoding='utf-8') as handle:
            for line in handle:
                batch.append(json.loads(line))
                if len(batch) >= 250:
                    self.add_sources(batch)
                    batch.clear()
        self.add_sources(batch)
        self.meta('sources_import_complete', 'true')

    def exclude_questions(self, questions):
        with self.lock, self.db:
            self.db.executemany('INSERT OR IGNORE INTO excluded_questions VALUES (?)', [(normalized(q),) for q in questions])

    def recover(self):
        with self.lock, self.db:
            self.db.execute("UPDATE sources SET status='pending' WHERE status='running'")

    def claim(self):
        with self.lock, self.db:
            row = self.db.execute("SELECT id,data FROM sources WHERE status='pending' ORDER BY rowid LIMIT 1").fetchone()
            if row is None:
                return None
            self.db.execute("UPDATE sources SET status='running' WHERE id=?", (row['id'],))
            return json.loads(row['data'])

    def mark_source(self, source, status, error=None):
        with self.lock, self.db:
            self.db.execute('UPDATE sources SET status=?,error=? WHERE id=?', (status, error, source))

    def source_counts(self):
        with self.lock:
            return dict(self.db.execute('SELECT status,COUNT(*) FROM sources GROUP BY status').fetchall())

    def queue_second_pass(self):
        """Reuse productive sources once, preserving document identity and the cap of4."""
        count = 0
        with self.lock, self.db:
            rows = self.db.execute("SELECT s.id,s.data,COUNT(q.seq) AS n FROM sources s JOIN samples q ON q.source=s.id WHERE s.status='done' GROUP BY s.id HAVING n BETWEEN 1 AND 3 ORDER BY s.rowid").fetchall()
            for row in rows:
                source = json.loads(row['data'])
                if source.get('generation_round', 1) >= 2:
                    continue
                source['generation_round'] = 2
                source['avoid_questions'] = [json.loads(r[0])['question'] for r in self.db.execute('SELECT data FROM samples WHERE source=?', (row['id'],))]
                self.db.execute("UPDATE sources SET status='pending',data=? WHERE id=?", (json.dumps(source, ensure_ascii=False), row['id']))
                count += 1
        return count

    def revalidate_samples(self):
        removed = 0
        with self.lock, self.db:
            rows = self.db.execute('SELECT q.seq,q.source,q.data,s.data AS source_data FROM samples q JOIN sources s ON s.id=q.source').fetchall()
            for row in rows:
                record = json.loads(row['data'])
                problems = single_target_violations(record['question']) + source_relevance_violations(json.loads(row['source_data']))
                if not problems:
                    continue
                self.db.execute('INSERT INTO rejects(source,reason,data) VALUES (?,?,?)', (row['source'], 'pilot_recheck:' + ','.join(problems), row['data']))
                self.db.execute('DELETE FROM samples WHERE seq=?', (row['seq'],))
                self._increment('accepted', -1)
                if record.get('question_type') == 'numeric_aggregation':
                    self._increment('numeric', -1)
                removed += 1
        return removed

    def accept(self, source, record):
        with self.lock, self.db:
            totals = self.totals()
            numeric = record.get('question_type') == 'numeric_aggregation'
            if totals['accepted'] >= self.target or (numeric and totals['numeric'] >= self.numeric_limit):
                return False
            key = normalized(record['question'])
            if self.db.execute('SELECT 1 FROM excluded_questions WHERE question_key=?', (key,)).fetchone():
                return False
            previous = self.db.execute('SELECT data FROM samples WHERE source=?', (source,)).fetchall()
            if len(previous) >= 4:
                return False
            for row in previous:
                question = json.loads(row['data'])['question']
                if difflib.SequenceMatcher(None, question.casefold(), record['question'].casefold()).ratio() > 0.88:
                    return False
            record = dict(record)
            identity = json.dumps({'question': record['question'], 'answer': record['answer'], 'supporting_chunk_ids': []}, sort_keys=True, ensure_ascii=False)
            record['qa_id'] = 'oceangraph_' + hashlib.sha256(identity.encode()).hexdigest()[:20]
            try:
                self.db.execute('INSERT INTO samples(source,question_key,qa_id,data) VALUES (?,?,?,?)',
                                (source, key, record['qa_id'], json.dumps(record, ensure_ascii=False)))
            except sqlite3.IntegrityError:
                return False
            self._increment('accepted', 1)
            if numeric:
                self._increment('numeric', 1)
            return True

    def reject(self, source, reason, record):
        with self.lock, self.db:
            self.db.execute('INSERT INTO rejects(source,reason,data) VALUES (?,?,?)',
                            (source, reason, json.dumps(record, ensure_ascii=False)))

    def snapshot(self):
        with self.lock:
            records = self.db.execute('SELECT seq,source,data FROM samples ORDER BY seq').fetchall()
            sources = {r['id']: json.loads(r['data']) for r in self.db.execute('SELECT id,data FROM sources')}
            return [(r['seq'], r['source'], json.loads(r['data'])) for r in records], sources

    def meta(self, key, value=None):
        with self.lock:
            if value is None:
                row = self.db.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
                return row[0] if row else None
            with self.db:
                self.db.execute('INSERT OR REPLACE INTO meta VALUES (?,?)', (key, str(value)))
