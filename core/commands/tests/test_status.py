from __future__ import annotations

import os
import unittest

from core.commands.status import status


class StatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_massive = os.environ.get("MASSIVE_API_KEY")
        self.original_workspace = os.environ.get("AUTOQUANT_WORKSPACE")

    def tearDown(self) -> None:
        if self.original_massive is None:
            os.environ.pop("MASSIVE_API_KEY", None)
        else:
            os.environ["MASSIVE_API_KEY"] = self.original_massive
        if self.original_workspace is None:
            os.environ.pop("AUTOQUANT_WORKSPACE", None)
        else:
            os.environ["AUTOQUANT_WORKSPACE"] = self.original_workspace

    def test_status_not_ok_when_required_env_missing(self) -> None:
        os.environ.pop("MASSIVE_API_KEY", None)
        os.environ.pop("AUTOQUANT_WORKSPACE", None)
        result = status()
        self.assertFalse(result["ok"])
        self.assertIn("MASSIVE_API_KEY", result["missing_env_vars"])
        self.assertIn("AUTOQUANT_WORKSPACE", result["missing_env_vars"])

    def test_status_ok_when_required_env_set(self) -> None:
        os.environ["MASSIVE_API_KEY"] = "abc"
        os.environ["AUTOQUANT_WORKSPACE"] = "/tmp/autoquant"
        result = status()
        self.assertTrue(result["ok"])
        self.assertEqual(result["missing_env_vars"], [])
        self.assertTrue(result["workspace"]["is_absolute"])


if __name__ == "__main__":
    unittest.main()
