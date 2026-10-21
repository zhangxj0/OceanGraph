import uuid
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    from oceangraph.batch.state import State, BudgetStop, arithmetic_violations
    from oceangraph.batch import state as batch_core
except ImportError:
    State = None
    BudgetStop = RuntimeError
    arithmetic_violations = None


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__).resolve().parent / ('test_' + uuid.uuid4().hex + '.sqlite')
        for suffix in ('', '-wal', '-shm'):
            self.addCleanup(Path(str(self.path) + suffix).unlink, missing_ok=True)

    def state(self, target=10, **kwargs):
        self.assertIsNotNone(State, 'Durable batch state is not implemented')
        return State(self.path, target=target, max_requests=3, max_input=1000, max_output=1000, **kwargs)

    def test_unknown_usage_reservation_survives_restart(self):
        s = self.state()
        s.reserve('generation', 'doc1', 100, 200)
        s.close()
        resumed = self.state()
        self.addCleanup(resumed.close)
        self.assertEqual(resumed.totals()['input_accounted'], 100)
        self.assertEqual(resumed.totals()['output_accounted'], 200)

    def test_reported_usage_releases_only_its_own_reservation(self):
        s = self.state()
        self.addCleanup(s.close)
        call = s.reserve('generation', 'doc1', 100, 200)
        s.reserve('generation', 'doc2', 100, 200)
        s.finish(call, 200, {'prompt_tokens': 20, 'completion_tokens': 30}, 'ok', 'stop')
        self.assertEqual(s.totals()['output_accounted'], 230)
        self.assertEqual(s.totals()['input_accounted'], 120)

    def test_request_cap_is_durable(self):
        s = self.state()
        self.addCleanup(s.close)
        for _ in range(3):
            s.reserve('generation', 'doc', 10, 10)
        with self.assertRaises(BudgetStop):
            s.reserve('generation', 'doc', 10, 10)

    def test_concurrent_acceptance_never_exceeds_target(self):
        s = self.state(target=5)
        self.addCleanup(s.close)
        with ThreadPoolExecutor(max_workers=8) as pool:
            accepted = list(pool.map(lambda i: s.accept('doc' + str(i), {'question': f'Which ocean mechanism is specific to region {i}?', 'answer': str(i), 'question_type': 'bridge'}), range(30)))
        self.assertEqual(sum(accepted), 5)
        self.assertEqual(s.totals()['accepted'], 5)

    def test_normalized_duplicate_rejected_after_restart(self):
        s = self.state()
        self.assertTrue(s.accept('d1', {'question': 'Which Current?', 'answer': 'Kuroshio', 'question_type': 'bridge'}))
        s.close()
        s = self.state()
        self.addCleanup(s.close)
        self.assertFalse(s.accept('d2', {'question': 'which current !', 'answer': 'Kuroshio', 'question_type': 'bridge'}))

    def test_document_cap_and_near_duplicate(self):
        s = self.state()
        self.addCleanup(s.close)
        first = {'question': 'Which named marine current transports the most heat near the coastal island in the winter season?', 'answer': 'A', 'question_type': 'bridge'}
        self.assertTrue(s.accept('d1', first))
        near = {**first, 'question': first['question'].replace('winter', 'summer')}
        self.assertFalse(s.accept('d1', near))
        for i, question in enumerate(('How does nitrogen availability affect phytoplankton growth offshore?',
                                      'When did elevated alkalinity peak at the deep station?',
                                      'Which species survived the cold treatment at low oxygen?')):
            self.assertTrue(s.accept('d1', {'question': question, 'answer': str(i), 'question_type': 'bridge'}))
        self.assertFalse(s.accept('d1', {'question': 'When did the bloom peak offshore?', 'answer': 'May', 'question_type': 'bridge'}))

    def test_numeric_quota(self):
        s = self.state(target=10, numeric_fraction=0.35)
        self.addCleanup(s.close)
        for i in range(3):
            self.assertTrue(s.accept(str(i), {'question': f'What is the numeric difference for site {i}?', 'answer': str(i), 'question_type': 'numeric_aggregation'}))
        self.assertFalse(s.accept('d4', {'question': 'What is the offshore ratio?', 'answer': '4', 'question_type': 'numeric_aggregation'}))

    def test_real_pilot_multi_target_and_dental_cases_are_rejected(self):
        self.assertTrue(hasattr(batch_core, 'single_target_violations'))
        self.assertTrue(hasattr(batch_core, 'source_relevance_violations'))
        self.assertTrue(batch_core.single_target_violations('Which bioturbating species has reduced Db, and by what mechanism did it feed head-down?'))
        self.assertTrue(batch_core.single_target_violations('For the macroalga, what extraction temperature and time were suitable?'))
        self.assertEqual(batch_core.single_target_violations('Which cold-water current feeds the western subarctic gyre?'), [])
        self.assertTrue(batch_core.source_relevance_violations({'title': 'Oral health of fishermen', 'chunks': ['Dental caries prevalence was compared in fishermen and non-fishermen.']}))
        self.assertEqual(batch_core.source_relevance_violations({'title': 'Marine oyster health', 'chunks': ['Oyster gill communities respond to ocean alkalinity enhancement.']}), [])

    def test_second_pass_preserves_source_id_and_is_bounded(self):
        s = self.state()
        self.addCleanup(s.close)
        s.add_sources([{'id': 'd1', 'topic': 'ocean'}, {'id': 'd2', 'topic': 'ocean'}])
        s.accept('d1', {'question': 'Which marine species fixes nitrogen offshore?', 'answer': 'A', 'question_type': 'bridge'})
        s.mark_source('d1', 'done')
        s.mark_source('d2', 'done')
        self.assertTrue(hasattr(s, 'queue_second_pass'))
        self.assertEqual(s.queue_second_pass(), 1)
        source = s.claim()
        self.assertEqual(source['id'], 'd1')
        self.assertEqual(source['generation_round'], 2)
        self.assertEqual(len(source['avoid_questions']), 1)
        s.mark_source('d1', 'done')
        self.assertEqual(s.queue_second_pass(), 0)

    def test_revalidation_removes_invalid_acceptance_without_refunding_usage(self):
        s = self.state()
        self.addCleanup(s.close)
        s.add_sources([{'id': 'd1', 'topic': 'ocean', 'title': 'Oral health of fishermen', 'chunks': ['Dental caries assessment.']}])
        s.accept('d1', {'question': 'What was the difference in dental caries?', 'answer': '38', 'question_type': 'numeric_aggregation'})
        s.reserve('generation', 'd1', 100, 100)
        self.assertTrue(hasattr(s, 'revalidate_samples'))
        self.assertEqual(s.revalidate_samples(), 1)
        self.assertEqual(s.totals()['accepted'], 0)
        self.assertEqual(s.totals()['numeric'], 0)
        self.assertEqual(s.totals()['requests'], 1)

    def test_recover_only_inflight_sources(self):
        s = self.state()
        self.addCleanup(s.close)
        s.add_sources([{'id': 'd1', 'topic': 'ocean'}, {'id': 'd2', 'topic': 'ocean'}])
        self.assertEqual(s.claim()['id'], 'd1')
        s.mark_source('d1', 'done')
        self.assertEqual(s.claim()['id'], 'd2')
        s.recover()
        self.assertEqual(s.claim()['id'], 'd2')

    def test_source_inventory_import_resumes_after_partial_commit(self):
        import json
        s = self.state()
        self.addCleanup(s.close)
        first, second = {'id': 'd1', 'topic': 'ocean'}, {'id': 'd2', 'topic': 'marine'}
        s.add_sources([first])
        path = self.path.with_suffix('.jsonl')
        self.addCleanup(path.unlink, missing_ok=True)
        path.write_text(json.dumps(first) + '\n' + json.dumps(second) + '\n', encoding='utf-8')
        self.assertTrue(hasattr(s, 'load_inventory'), 'Resumable source import is not implemented')
        s.load_inventory(path)
        self.assertEqual(s.source_counts(), {'pending': 2})
        self.assertEqual(s.meta('sources_import_complete'), 'true')

    def test_supervisor_failure_signals_stop_before_pool_wait(self):
        import threading
        self.assertIsNotNone(State, 'Core is not implemented')
        self.assertTrue(hasattr(batch_core, 'supervise'), 'Fail-closed supervisor is not implemented')
        stop = threading.Event()
        def fail():
            raise OSError('Simulated export failure')
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(lambda: stop.wait(1))
            with self.assertRaises(OSError):
                batch_core.supervise([future], stop, fail, interval=0.001)
            self.assertTrue(stop.is_set())
            self.assertTrue(future.result(timeout=0.2))

    def test_exhausted_or_stopped_run_cannot_restart(self):
        self.assertTrue(hasattr(batch_core, 'check_run_allowed'), 'Runtime/STOP preflight is not implemented')
        with self.assertRaises(BudgetStop):
            batch_core.check_run_allowed(True, 0, 10)
        with self.assertRaises(BudgetStop):
            batch_core.check_run_allowed(False, 10, 10)
        batch_core.check_run_allowed(False, 9, 10)

    def test_absolute_watchdog_fires_independent_of_workers(self):
        import threading
        self.assertTrue(hasattr(batch_core, 'start_watchdog'), 'Absolute watchdog is not implemented')
        fired = threading.Event()
        timer = batch_core.start_watchdog(0.02, fired.set)
        self.addCleanup(timer.cancel)
        self.assertTrue(fired.wait(1))

    def numeric(self, answer='56.9%'):
        return {'question': 'In the Moorea reef projection, what was the relative reduction in coral cover? Round to one decimal place.',
                'answer': answer, 'question_type': 'numeric_aggregation',
                'calculation': {'operation': 'percentage_reduction', 'decimals': 1,
                                'operands': [{'value': '67.1', 'source_quote': 'ambient coral cover reached 67.1%'},
                                             {'value': '28.9', 'source_quote': 'OA coral cover reached 28.9%'}]}}

    def test_arithmetic_catches_the_actual_56_percent_error(self):
        self.assertIsNotNone(arithmetic_violations, 'Arithmetic check is not implemented')
        context = 'The ambient coral cover reached 67.1%. The OA coral cover reached 28.9%.'
        self.assertTrue(arithmetic_violations(self.numeric('56%'), context))
        self.assertEqual(arithmetic_violations(self.numeric(), context), [])

    def test_invented_operand_and_question_with_all_inputs_rejected(self):
        self.assertIsNotNone(arithmetic_violations, 'Arithmetic check is not implemented')
        context = 'The ambient coral cover reached 67.1%. The OA coral cover reached 28.9%.'
        q = self.numeric()
        q['calculation']['operands'][0]['value'] = '66.1'
        self.assertIn('operand_not_in_quote', arithmetic_violations(q, context))
        q = self.numeric()
        q['question'] += ' Values are 67.1 and 28.9.'
        self.assertIn('all_operands_in_question', arithmetic_violations(q, context))


if __name__ == '__main__':
    unittest.main()
