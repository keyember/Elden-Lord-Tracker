import unittest
from tracker.run_clock import RunClock
class RunClockTests(unittest.TestCase):
    def test_pause_and_resume(self):
        c=RunClock(10)
        c.sample(0,True);c.sample(.1,True)
        self.assertAlmostEqual(c.seconds,10.1)
        c.sample(.2,False);c.sample(.3,False);c.sample(.4,True)
        self.assertAlmostEqual(c.seconds,10.1)
        c.sample(.5,True);self.assertAlmostEqual(c.seconds,10.2)
    def test_gap(self):
        c=RunClock();c.sample(0,True);c.sample(2,True)
        self.assertEqual(c.seconds,0)
    def test_saved_resume(self):
        c=RunClock(3661);self.assertEqual(c.formatted(),"01:01:01")
        c.freeze();c.sample(200,True);self.assertEqual(c.seconds,3661)
    def test_invalid_duration(self):
        with self.assertRaises(ValueError):RunClock(-1)
        with self.assertRaises(ValueError):RunClock(float('nan'))
