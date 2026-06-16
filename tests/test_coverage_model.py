import unittest

from tools.coverage_model import classify_case, coverage_summary
from tools.packet_gen import coverage_closure_cases, directed_cases, make_ipv4_udp_frame, random_cases


class CoverageModelTest(unittest.TestCase):
    def test_valid_udp_min_packet_classification(self):
        case = make_ipv4_udp_frame("basic").to_json_dict()
        row = classify_case(case)
        self.assertEqual(row["vlan"], "no_vlan")
        self.assertEqual(row["ethertype"], "ipv4")
        self.assertEqual(row["ipv4"], "valid_ipv4")
        self.assertEqual(row["udp"], "valid_udp")
        self.assertEqual(row["frame_length"], "min_udp")

    def test_directed_cases_hit_negative_bins(self):
        summary = coverage_summary(case.to_json_dict() for case in directed_cases())
        self.assertGreater(summary["negative_count"], 0)
        self.assertIn(("short_unknown", "short_eth", "no_ipv4", "no_udp", "short_eth"), summary["matrix_counts"])

    def test_coverage_closure_hits_all_required_bins(self):
        summary = coverage_summary(case.to_json_dict() for case in coverage_closure_cases())
        self.assertEqual(summary["missed_required"], [])

    def test_random_cases_include_closure_and_backpressure_bins(self):
        cases = [case.to_json_dict() for case in random_cases(64, seed=123)]
        summary = coverage_summary(cases)
        self.assertEqual(summary["missed_required"], [])
        self.assertGreater(summary["backpressure_counts"]["input_gaps"], 0)
        self.assertGreater(summary["backpressure_counts"]["meta_ready_stalls"], 0)
        self.assertGreater(summary["backpressure_counts"]["input_and_meta"], 0)


if __name__ == "__main__":
    unittest.main()
