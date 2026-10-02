# SPDX-License-Identifier: GPL-3.0-only
"""Synthetic registry/session tests; no game process, save or user history is touched."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
NEW_IDS = ('flag_30110800', 'flag_30040800')

class ClassicArenaUpdateTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = json.loads((ROOT / 'tracker/catalogue_data/combat_catalog.json').read_text(encoding='utf-8'))
        self.config_path = Path(self.temp.name) / 'combat_catalog.json'
        self.config_path.write_text(json.dumps(self.config), encoding='utf-8')
        prefix = '_classic_arena_test_fixture'
        package = types.ModuleType(prefix)
        package.__path__ = [str(ROOT / 'tracker')]
        catalog = types.ModuleType(prefix + '.boss_catalog')
        catalog.BY_ID = {key: dict(id=key, flag_id=int(key[5:]) if key.startswith('flag_') else -1, content='base_game') for key in self.config['encounters']}
        catalog.BOSSES = tuple(catalog.BY_ID.values())
        catalog.active_bosses = lambda: tuple(catalog.BY_ID.values())
        catalog.display_name = lambda key, language=None: key
        translations = types.ModuleType(prefix + '.i18n')
        translations.tr = lambda value, language=None: value
        translations.settings = lambda: {'include_dlc': True}
        translations.get_language = lambda: 'fr'
        context = patch.dict(sys.modules, {prefix: package, prefix + '.boss_catalog': catalog, prefix + '.i18n': translations})
        context.start()
        self.addCleanup(context.stop)
        self.registry = self.load(prefix + '.combat_registry', ROOT / 'tracker/combat_registry.py')
        self.registry.CONFIG_PATH = self.config_path
        self.tracking = self.load(prefix + '.combat_tracking', ROOT / 'tracker/combat_tracking.py')

    @staticmethod
    def load(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    def save(self):
        self.config_path.write_text(json.dumps(self.config), encoding='utf-8')

    def snap(self, key, active=False, victory=False, can_count=True):
        return dict(can_count=can_count, combat_signal=dict(boss_id=key, active=active, victory=victory), screen_state=0, name_match=True)

    def started(self, key):
        session = self.tracking.CombatSession(boss_id=key)
        session.observe(self.snap(key), 0, 0)
        session.observe(self.snap(key, True), 1, 0)
        return session

    def test_valid_configuration_has_207_encounters_and_12_supported(self):
        entries, error = self.registry.read_configuration()
        self.assertIsNone(error)
        self.assertEqual(len(entries), 207)
        self.assertEqual(len(self.registry.supported_specs(False)), self._expected_supported_count())

    def test_two_classic_specs_have_exact_explicit_flags(self):
        for key, active, victory in [('flag_30110800', 30112805, 30110800), ('flag_30040800', 30042805, 30040800)]:
            with self.subTest(key=key):
                spec = self.registry.supported_spec(key)
                self.assertEqual(spec['active_flag'], active)
                self.assertEqual(spec['victory_flag'], victory)
                self.assertEqual(spec['validation'], self.config['encounters'][key]['validation'])
                self.assertEqual(self.config['encounters'][key]['evidence']['pc_tested'], self.config['encounters'][key]['validation'] == 'user_tested')

    def test_summary_distinguishes_user_tested_and_documented(self):
        summary = self.registry.catalogue_view()['summary']
        self.assertEqual(summary['user_tested'], sum((item['validation'] == 'user_tested' for item in self.config['encounters'].values())))
        self.assertEqual(summary['documented'], sum((item['validation'] == 'documented' for item in self.config['encounters'].values())))
        self.assertEqual(summary['catalogue_total'], 207)

    def test_existing_godefroy_flag_and_evidence_remain(self):
        item = self.config['encounters']['flag_1039500800']
        self.assertEqual(item['active_flag'], 1039502806)
        self.assertEqual(item['evidence']['entry'], 'four_run_trace')

    def test_crucible_status_is_user_reported_not_new_trace(self):
        item = self.config['encounters']['flag_1042370800']
        self.assertEqual(item['validation'], 'user_tested')
        self.assertEqual(item['active_flag'], 1042372806)
        self.assertEqual(item['evidence']['verification'], 'user_reported_full_tracking')

    def test_bad_source_path_is_rejected(self):
        self.config['encounters'][NEW_IDS[0]]['source']['path'] = 'wrong.py'
        self.save()
        self.assertIsNotNone(self.registry.read_configuration()[1])

    def test_phase_flag_substitution_is_rejected(self):
        self.config['encounters'][NEW_IDS[0]]['active_flag'] = 30112802
        self.save()
        self.assertIsNotNone(self.registry.read_configuration()[1])

    def test_boolean_flag_is_rejected(self):
        self.config['encounters'][NEW_IDS[0]]['active_flag'] = True
        self.save()
        self.assertIsNotNone(self.registry.read_configuration()[1])

    def test_duplicate_active_flag_is_rejected(self):
        self.config['encounters']['flag_1042370800']['active_flag'] = 1039502806
        self.save()
        self.assertIsNotNone(self.registry.read_configuration()[1])

    def test_disabled_spec_is_not_returned(self):
        self.config['encounters'][NEW_IDS[0]]['enabled'] = False
        self.save()
        self.assertIsNone(self.registry.supported_spec(NEW_IDS[0]))
        self.assertEqual(len(self.registry.supported_specs(False)), self._expected_supported_count())

    def test_32_guard_remains(self):
        for index in range(21):
            key = 'synthetic_' + str(index)
            self.registry.BY_ID[key] = dict(id=key, flag_id=800000 + index)
            self.config['encounters'][key] = dict(active_flag=900000 + index, validation='user_tested')
        self.save()
        self.assertIn('32', self.registry.read_configuration()[1])

    def test_stable_active_signal_counts_one_attempt(self):
        for key in NEW_IDS:
            with self.subTest(key=key):
                session = self.started(key)
                for seconds in range(2, 8):
                    session.observe(self.snap(key, True), seconds, 0)
                self.assertEqual(session.attempts, 1)

    def test_joining_midfight_does_not_invent_attempt(self):
        for key in NEW_IDS:
            session = self.tracking.CombatSession(boss_id=key)
            session.observe(self.snap(key, True), 0, 0)
            self.assertEqual(session.attempts, 0)
            self.assertEqual(session.phase, 'active_untracked')

    def test_death_waits_for_reset_before_second_attempt(self):
        for key in NEW_IDS:
            session = self.started(key)
            session.observe(self.snap(key, True), 2, 1)
            self.assertEqual(session.last_result, 'death')
            session.observe(self.snap(key, True), 3, 1)
            self.assertEqual(session.attempts, 1)
            session.observe(self.snap(key), 4, 1)
            session.observe(self.snap(key, True), 5, 1)
            self.assertEqual(session.attempts, 2)
            self.assertEqual(session.observed_boss_deaths, 1)

    def test_victory_is_not_a_death(self):
        for key in NEW_IDS:
            session = self.started(key)
            session.observe(self.snap(key, True, True), 2, 0)
            self.assertEqual(session.last_result, 'victory')
            self.assertEqual(session.observed_boss_deaths, 0)

    def test_simultaneous_victory_and_death_is_counted_once(self):
        for key in NEW_IDS:
            session = self.started(key)
            session.observe(self.snap(key, True, True), 2, 1)
            self.assertEqual(session.last_result, 'victory_and_death')
            self.assertEqual(session.observed_boss_deaths, 1)
            self.assertEqual(self.tracking.count_observed_boss_deaths(session.events, key), 1)

    def test_missing_signal_with_death_is_uncertain(self):
        session = self.started(NEW_IDS[0])
        session.observe(dict(can_count=False, screen_state=1), 2, 1)
        self.assertEqual(session.last_result, 'uncertain')
        self.assertEqual(session.observed_boss_deaths, 0)

    def test_counter_jump_is_not_assigned_as_one_boss_death(self):
        session = self.started(NEW_IDS[0])
        session.observe(self.snap(NEW_IDS[0], True), 2, 2)
        self.assertEqual(session.last_result, 'uncertain')
        self.assertEqual(session.observed_boss_deaths, 0)

    def test_histories_remain_independent_and_merge_idempotent(self):
        current = {'combat_history': [dict(id='unrelated', type='note', boss_id='other')]}
        for key in NEW_IDS:
            session = self.started(key)
            session.observe(self.snap(key, True), 2, 1)
            session.merge(current)
            length = len(current['combat_history'])
            session.merge(current)
            self.assertEqual(len(current['combat_history']), length)
        self.assertEqual(current['combat_history'][0]['id'], 'unrelated')
        for key in NEW_IDS:
            self.assertEqual(self.tracking.count_observed_boss_deaths(current['combat_history'], key), 1)

    def test_legacy_godefroy_history_remains_readable(self):
        key = 'flag_1039500800'
        history = [dict(id='old-start', type='boss_attempt_start', boss_id=key, tracking_mode='godefroy_active_flag_v1', attempt_id='old'), dict(id='old-end', type='boss_attempt_end', boss_id=key, tracking_mode='godefroy_active_flag_v1', attempt_id='old', outcome='death')]
        original = copy.deepcopy(history)
        session = self.tracking.CombatSession(history, 1, boss_id=key)
        self.assertEqual(session.attempts, 1)
        self.assertEqual(session.observed_boss_deaths, 1)
        self.assertEqual(history, original)

    def _expected_supported_count(self):
        return sum((item.get('validation') in ('documented', 'user_tested') and item.get('enabled', True) is not False for item in self.config['encounters'].values()))
if __name__ == '__main__':
    unittest.main()
