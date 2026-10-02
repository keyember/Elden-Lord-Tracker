import unittest
import tempfile
from pathlib import Path
from tracker import profiles

class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.old=(profiles.DIRECTORY,profiles.SELECTION)
        profiles.DIRECTORY=Path(self.temp.name)/"profiles"
        profiles.SELECTION=Path(self.temp.name)/"selection.json"
    def tearDown(self):
        profiles.DIRECTORY,profiles.SELECTION=self.old
        self.temp.cleanup()
    def test_independent_profiles(self):
        a=profiles.create_profile("save.sl2",0,"RL1")
        b=profiles.create_profile("save.sl2",0,"Naked")
        self.assertNotEqual(a["id"],b["id"])
        self.assertEqual(len(profiles.list_profiles("save.sl2",0)),2)
        self.assertEqual(profiles.list_profiles("save.sl2",1),[])
    def test_selection_persisted_and_scoped(self):
        a=profiles.create_profile("save.sl2",0,"RL1")
        profiles.select_profile(a)
        self.assertEqual(profiles.selected_profile("save.sl2",0)["name"],"RL1")
        self.assertIsNone(profiles.selected_profile("save.sl2",1))
        self.assertIsNone(profiles.selected_profile("other.sl2",0))
    def test_bad_name(self):
        with self.assertRaises(ValueError):profiles.create_profile("save.sl2",0," ")
