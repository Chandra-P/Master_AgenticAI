"""Run CI evaluation checks with Python outbound sockets prohibited, including the CLI baseline."""

import runpy
import socket
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


def forbidden(*args, **kwargs):
    raise AssertionError("Outbound network is prohibited during offline evaluation checks")


def main():
    with (
        patch.object(socket.socket, "connect", forbidden),
        patch.object(socket.socket, "connect_ex", forbidden),
        patch.object(socket, "create_connection", forbidden),
    ):
        code = pytest.main(
            [
                "tests/test_evaluation_dataset.py",
                "tests/test_evaluation_graders.py",
                "tests/test_evaluation_runner.py",
                "tests/test_evaluation_privacy.py",
                "tests/test_evaluation_live_inputs.py",
                "-q",
                "--basetemp=runtime/ci-tests",
            ]
        )
        if code:
            raise SystemExit(code)
        sys.argv = [
            "run_evals.py",
            "--mode",
            "offline",
            "--runtime",
            "runtime/ci",
            "--summary-export",
            "runtime/ci-summary.json",
        ]
        runpy.run_path(str(Path(__file__).with_name("run_evals.py")), run_name="__main__")


if __name__ == "__main__":
    main()
