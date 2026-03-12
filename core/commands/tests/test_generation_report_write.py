from __future__ import annotations

import os
import tempfile
import unittest

from core.commands.write_generation_report import write_generation_report
from core.commands.shared import ensure_run_layout, generation_report_path, write_run_meta
from core.paths import run_dir
from core.schemas import RunMeta
from core.utils.time_utils import now_utc


class WriteGenerationReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_workspace = os.environ.get("AUTOQUANT_WORKSPACE")
        os.environ["AUTOQUANT_WORKSPACE"] = self.temp_dir.name
        self.run_id = "testrun"
        ensure_run_layout(run_dir(self.run_id))
        write_run_meta(
            RunMeta(
                run_id=self.run_id,
                ticker="AAPL",
                from_date="2025-01-01",
                to_date="2025-06-30",
                created_at_utc=now_utc(),
            )
        )

    def tearDown(self) -> None:
        if self.original_workspace is None:
            os.environ.pop("AUTOQUANT_WORKSPACE", None)
        else:
            os.environ["AUTOQUANT_WORKSPACE"] = self.original_workspace
        self.temp_dir.cleanup()

    def test_write_generation_report_uses_expected_path(self) -> None:
        result = write_generation_report(self.run_id, 2, "# Generation 2\n\nLearned something")
        path = generation_report_path(self.run_id, 2)
        self.assertEqual(result["report_path"], str(path))
        self.assertTrue(path.exists())
        self.assertEqual(path.read_text(encoding="utf-8"), "# Generation 2\n\nLearned something\n")

    def test_write_generation_report_creates_template_when_content_is_empty(self) -> None:
        write_generation_report(self.run_id, 0, "")
        content = generation_report_path(self.run_id, 0).read_text(encoding="utf-8")
        self.assertEqual(
            content,
            "# Generation 0\n\n## What I learned\n\n## How this informs the next generation\n\n## Next generation plan\n",
        )


if __name__ == "__main__":
    unittest.main()
