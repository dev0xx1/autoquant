from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.commands.register_model import register_model
from core.commands.shared import ensure_run_layout, write_run_meta
from core.constants import MODELS_CSV
from core.paths import run_dir, tmp_root
from core.schemas import RunMeta
from core.utils.storage import get_model_rows
from core.utils.time_utils import now_utc


class RegisterModelTests(unittest.TestCase):
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
                task="classification",
                created_at_utc=now_utc(),
            )
        )
        self.model_path = Path(self.temp_dir.name) / "candidate.py"
        self.model_path.write_text("class Candidate:\n    pass\n", encoding="utf-8")

    def tearDown(self) -> None:
        if self.original_workspace is None:
            os.environ.pop("AUTOQUANT_WORKSPACE", None)
        else:
            os.environ["AUTOQUANT_WORKSPACE"] = self.original_workspace
        self.temp_dir.cleanup()

    def test_register_model_raises_when_validation_fails(self) -> None:
        with patch(
            "core.commands.validate_model.validate_model",
            return_value={"status": "failed", "error": "bad model"},
        ):
            with self.assertRaises(RuntimeError):
                register_model(
                    run_id=self.run_id,
                    name="candidate",
                    model_path=str(self.model_path),
                    log="test",
                    reasoning="test",
                )
        models = get_model_rows(run_dir(self.run_id), MODELS_CSV)
        self.assertEqual(models, [])

    def test_register_model_registers_after_validation(self) -> None:
        with patch(
            "core.commands.validate_model.validate_model",
            return_value={
                "status": "completed",
                "validation_run_id": "sandbox",
                "model_id": "abc12345",
                "metrics": {"accuracy": 0.7, "f1": 0.6, "macro_f1": 0.6, "weighted_f1": 0.6},
            },
        ) as mocked_validate:
            result = register_model(
                run_id=self.run_id,
                name="candidate",
                model_path=str(self.model_path),
                log="test",
                reasoning="test",
            )
        mocked_validate.assert_called_once()
        models = get_model_rows(run_dir(self.run_id), MODELS_CSV)
        self.assertEqual(len(models), 1)
        self.assertEqual(result["run_id"], self.run_id)
        self.assertEqual(result["name"], "candidate")
        self.assertEqual(result["validation"]["status"], "completed")
        self.assertEqual(result["validation"]["validation_run_id"], "sandbox")
        self.assertTrue(tmp_root().exists())


if __name__ == "__main__":
    unittest.main()
