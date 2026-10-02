import unittest
from tracker.run_clock import RunClock

class TestConsolidatedRunClock(unittest.TestCase):
    def test_initial_sample_adds_nothing(self):
        c=RunClock(10);self.assertEqual(c.sample(100,True),10)
    def test_active_intervals(self):
        c=RunClock();c.sample(0,True);c.sample(.1,True);c.sample(.2,True)
        self.assertAlmostEqual(c.seconds,.2)
    def test_pause_entry_is_not_counted(self):
        c=RunClock();c.sample(0,True);c.sample(.1,False);self.assertEqual(c.seconds,0)
    def test_pause_exit_is_not_counted(self):
        c=RunClock();c.sample(0,False);c.sample(.1,True);c.sample(.2,True)
        self.assertAlmostEqual(c.seconds,.1)
    def test_long_gap_skipped(self):
        c=RunClock(5);c.sample(0,True);c.sample(10,True);self.assertEqual(c.seconds,5)
    def test_half_second_limit_unchanged(self):
        c=RunClock();c.sample(0,True);c.sample(.5,True);self.assertEqual(c.seconds,0)
    def test_backwards_interval_skipped(self):
        c=RunClock(5);c.sample(10,True);c.sample(9,True);self.assertEqual(c.seconds,5)
    def test_freeze_prevents_catchup(self):
        c=RunClock(5);c.sample(0,True);c.freeze();c.sample(100,True);self.assertEqual(c.seconds,5)
    def test_format(self):
        self.assertEqual(RunClock(3661.9).formatted(),'01:01:01')
    def test_invalid_saved_time(self):
        for value in [True,-1,float('nan'),float('inf'),None,'bad']:
            with self.subTest(value=value),self.assertRaises(ValueError):RunClock(value)
    def test_invalid_timestamp(self):
        for value in [True,float('nan'),float('inf'),'1',None]:
            with self.subTest(value=value),self.assertRaises(ValueError):RunClock().sample(value,True)
    def test_invalid_permission(self):
        for value in [1,0,'yes',None]:
            with self.subTest(value=value),self.assertRaises(ValueError):RunClock().sample(0,value)

if __name__=='__main__':
    unittest.main(verbosity=2)
