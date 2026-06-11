import unittest

from tools.packet_gen import directed_cases, make_ipv4_udp_frame


class PacketGenTest(unittest.TestCase):
    def test_directed_case_count(self):
        self.assertEqual(len(directed_cases()), 18)

    def test_min_udp_frame_shape(self):
        case = make_ipv4_udp_frame("basic")
        self.assertEqual(len(case.frame), 42)
        self.assertEqual(case.frame[12:14], b"\x08\x00")
        self.assertEqual(case.frame[23], 17)


if __name__ == "__main__":
    unittest.main()
