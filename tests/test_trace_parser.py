import tempfile
import unittest
from pathlib import Path

from tools.parse_trace import parse_trace


class TraceParserTest(unittest.TestCase):
    def test_counts_metadata_and_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trace.log"
            path.write_text(
                "cycle=1 event=byte data=0xff sop=1 eop=0 state=1 byte_idx=0 in_ready=1\n"
                "cycle=2 event=meta ready=1 frame_len=42 error_udp_length=1\n",
                encoding="utf-8",
            )
            stats = parse_trace(path)
        self.assertEqual(stats["bytes"], 1)
        self.assertEqual(stats["packets"], 1)
        self.assertEqual(stats["errors"]["error_udp_length"], 1)


if __name__ == "__main__":
    unittest.main()
