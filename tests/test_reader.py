import unittest
import hashlib
import struct
from tracker.save_reader import STRIDE, SUMMARY, NAME, validate_slot, read_names, read_profile, format_time

class ReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        payload = bytes(STRIDE-16)
        block = hashlib.md5(payload).digest()+payload
        data = bytearray(b"BND4"+bytes(0x300-4)+block*10+bytes(0x60010))
        for slot in range(10):
            a = NAME+slot*0x24C
            name = f"Test {slot}".encode("utf-16le")
            data[a:a+len(name)] = name
            struct.pack_into("<I",data,a+0x22,50)
            struct.pack_into("<I",data,a+0x26,82808)
        data[SUMMARY:SUMMARY+16] = hashlib.md5(data[SUMMARY+16:SUMMARY+0x60010]).digest()
        cls.data=bytes(data)
    def test_slots(self):
        for i in range(10): validate_slot(self.data,i)
    def test_names(self):
        self.assertEqual(read_names(self.data)[3],"Test 3")
    def test_profile(self):
        self.assertEqual(read_profile(self.data,4)["timer"],"23:00:08")
    def test_corruption(self):
        d=bytearray(self.data);d[0x320]^=1
        with self.assertRaises(ValueError):validate_slot(d,0)
    def test_summary_corruption(self):
        d=bytearray(self.data);d[NAME]^=1
        with self.assertRaises(ValueError):read_names(d)
    def test_time(self):
        self.assertEqual(format_time(360001),"100:00:01")
    def test_invalid_slot(self):
        with self.assertRaises(ValueError):validate_slot(self.data,10)
