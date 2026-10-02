import unittest
from tracker.combat_tracking import CombatSession, BOSS_ID

class TestExperimentalCombat(unittest.TestCase):
    def snap(self,active,victory=False):
        return dict(can_count=True,combat_signal=dict(boss_id=BOSS_ID,active=active,victory=victory))
    def test_four_deaths(self):
        c=CombatSession(tracked_deaths=10)
        for i in range(4):
            c.observe(self.snap(False),i*10,10+i)
            c.observe(self.snap(True),i*10+1,10+i)
            c.observe(self.snap(True),i*10+2,11+i)
            for _ in range(3):c.observe(self.snap(True),i*10+3,11+i)
            self.assertEqual(c.attempts,i+1)
        self.assertEqual(sum(e.get('outcome')=='death' for e in c.events),4)
    def test_start_midfight_not_counted(self):
        c=CombatSession();c.observe(self.snap(True),1,0)
        self.assertEqual(c.attempts,0);self.assertEqual(c.phase,'active_untracked')
    def test_repeat_true_not_duplicate(self):
        c=CombatSession();c.observe(self.snap(False),0,0)
        for t in range(1,10):c.observe(self.snap(True),t,0)
        self.assertEqual(c.attempts,1)
    def test_pause_not_new_attempt(self):
        c=CombatSession();c.observe(self.snap(False),0,0);c.observe(self.snap(True),1,0)
        c.observe(dict(can_count=False),2,0);c.observe(self.snap(True),3,0)
        self.assertEqual(c.attempts,1);self.assertEqual(c.phase,'active')
    def test_false_after_pause_unknown_result(self):
        c=CombatSession();c.observe(self.snap(False),0,0);c.observe(self.snap(True),1,0)
        c.observe(dict(can_count=False),2,0);c.observe(self.snap(False),3,0)
        self.assertEqual(c.events[-1]['outcome'],'interrupted')
    def test_victory(self):
        c=CombatSession();c.observe(self.snap(False),0,0);c.observe(self.snap(True),1,0);c.observe(self.snap(True,True),2,0)
        self.assertEqual(c.events[-1]['outcome'],'victory')
    def test_simultaneous_victory_death(self):
        c=CombatSession();c.observe(self.snap(False),0,0);c.observe(self.snap(True),1,0);c.observe(self.snap(True,True),2,1)
        self.assertEqual(c.events[-1]['outcome'],'victory_and_death')
    def test_death_during_unknown_not_attributed(self):
        c=CombatSession();c.observe(self.snap(False),0,0);c.observe(self.snap(True),1,0);c.observe(dict(can_count=True),2,1)
        self.assertEqual(c.events[-1]['outcome'],'uncertain')
    def test_counter_gap(self):
        c=CombatSession();c.observe(self.snap(False),0,0);c.observe(self.snap(True),1,0);c.observe(self.snap(True),2,3)
        self.assertEqual(c.events[-1]['outcome'],'uncertain')
    def test_disarmed_by_unknown_before_start(self):
        c=CombatSession();c.observe(self.snap(False),0,0);c.observe(dict(can_count=False),1,0);c.observe(self.snap(True),2,0)
        self.assertEqual(c.attempts,0)
    def test_merge_idempotent(self):
        c=CombatSession();c.observe(self.snap(False),0,0);c.observe(self.snap(True),1,0);current={};c.merge(current);c.merge(current)
        self.assertEqual(len(current['combat_history']),1)
    def test_restart_orphan_is_interrupted(self):
        c=CombatSession();c.observe(self.snap(False),0,0);c.observe(self.snap(True),1,0)
        next_session=CombatSession(c.events,0)
        self.assertEqual(next_session.attempts,1);self.assertEqual(next_session.events[0]['outcome'],'interrupted');self.assertIsNone(next_session.events[0]['run_seconds'])
    def test_stop(self):
        c=CombatSession();c.observe(self.snap(False),0,0);c.observe(self.snap(True),1,0);c.stop(2)
        self.assertEqual(c.events[-1]['outcome'],'interrupted');self.assertEqual(c.phase,'stopped')
    def test_unrelated_history_not_imported(self):
        c=CombatSession([{'type':'boss_victory','boss_id':BOSS_ID}]);self.assertEqual(c.attempts,0)

if __name__=='__main__':unittest.main(verbosity=2)
