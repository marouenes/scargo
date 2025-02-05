import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_mock import MockerFixture
from pytest_subprocess import FakeProcess

from scargo.commands.test import scargo_test
from scargo.config import Config


def test_scargo_test_no_test_dir(  # type: ignore[no-any-unimported]
    config: Config,
    fs: FakeFilesystem,
    caplog: pytest.LogCaptureFixture,
    mock_prepare_config: MagicMock,
) -> None:
    config.project_root = Path(".")
    with pytest.raises(SystemExit) as e:
        scargo_test(False)
        assert e.value.code == 1
    assert "Directory `tests` does not exist." in caplog.text


def test_scargo_test_no_cmake_file(  # type: ignore[no-any-unimported]
    config: Config,
    caplog: pytest.LogCaptureFixture,
    mock_prepare_config: MagicMock,
    fs: FakeFilesystem,
) -> None:
    config.project_root = Path(".")
    os.mkdir("tests")
    with pytest.raises(SystemExit) as e:
        scargo_test(False)
        assert e.value.code == 1
    assert "Directory `tests`: File `CMakeLists.txt` does not exist." in caplog.text


def test_scargo_test(  # type: ignore[no-any-unimported]
    config: Config, fp: FakeProcess, fs: FakeFilesystem, mock_prepare_config: MagicMock
) -> None:
    config.project_root = Path(".")
    subprocess_commands = [
        ["conan", "profile", "list"],
        ["conan", "profile", "detect"],
        ["conan", "remote", "list-users"],
        ["conan", "source", "."],
        [
            "conan",
            "install",
            Path("tests"),
            "-of",
            Path("build/tests"),
            "-sbuild_type=Debug",
            "-b",
            "missing",
        ],
        [
            "conan",
            "build",
            "-of",
            Path("build/tests"),
            Path("tests"),
            "-sbuild_type=Debug",
            "-b",
            "missing",
        ],
        ["ctest"],
        ["gcovr", "-r", "ut", ".", "-f", Path("src"), "--html=ut-coverage.html"],
    ]

    for command in subprocess_commands:
        fp.register(command)  # type: ignore[arg-type]

    Path("tests").mkdir()
    Path("tests/CMakeLists.txt").touch()
    scargo_test(False)

    # assert correct order
    assert list(fp.calls) == subprocess_commands


@pytest.fixture
def mock_prepare_config(mocker: MockerFixture, config: Config) -> MagicMock:
    return mocker.patch(f"{scargo_test.__module__}.prepare_config", return_value=config)
