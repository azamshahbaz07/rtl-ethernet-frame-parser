import unittest

from tools.packet_gen import IPPROTO_TCP, directed_cases, make_ipv4_udp_frame


class PacketGenTest(unittest.TestCase):
    def test_directed_case_count(self):
        self.assertEqual(len(directed_cases()), 18)

    def test_min_udp_frame_shape(self):
        case = make_ipv4_udp_frame("basic")
        self.assertEqual(len(case.frame), 42)
        self.assertEqual(case.frame[12:14], b"\x08\x00")
        self.assertEqual(case.frame[23], 17)

    def test_non_udp_ipv4_total_length_matches_payload_only(self):
        case = make_ipv4_udp_frame("tcp", ipv4_protocol=IPPROTO_TCP, payload=b"payload")
        self.assertEqual(case.frame[16:18], (20 + len(b"payload")).to_bytes(2, "big"))


if __name__ == "__main__":
    unittest.main()
