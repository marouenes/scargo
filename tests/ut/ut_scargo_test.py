from pathlib import Path

import pytest
from pytest_subprocess import FakeProcess

from scargo.commands.test import run_it, run_ut, scargo_test
from scargo.config import Config
from tests.ut.utils import get_test_project_config

PROJECT_ROOT_PATH = Path("root_path")
TEST_SRC_DIR = Path(PROJECT_ROOT_PATH, "tests")
TEST_BUILD_DIR = Path(PROJECT_ROOT_PATH, "build", "tests")
GCOV_EXECUTABLE = "gcov_executable_example"


@pytest.fixture
def mock_get_project_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "scargo.commands.test.get_project_root", lambda: PROJECT_ROOT_PATH
    )


@pytest.fixture
def config(monkeypatch: pytest.MonkeyPatch) -> Config:
    test_project_config = get_test_project_config()

    test_project_config.tests.gcov_executable = GCOV_EXECUTABLE

    monkeypatch.setattr(
        "scargo.commands.test.prepare_config",
        lambda: test_project_config,
    )

    return test_project_config


def test_scargo_test(
    config: Config,
    mock_get_project_root: None,
    fp: FakeProcess,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # ARRANGE
    monkeypatch.setattr(Path, "exists", lambda _: True)
    monkeypatch.setattr("scargo.commands.test.run_ut", lambda *_: None)

    conan_install_cmd = [
        "conan",
        "install",
        str(TEST_SRC_DIR),
        "-if",
        str(TEST_BUILD_DIR),
    ]
    conan_build_cmd = ["conan", "build", str(TEST_SRC_DIR), "-bf", str(TEST_BUILD_DIR)]

    fp.register(conan_install_cmd)
    fp.register(conan_build_cmd)

    # ACT
    scargo_test(False)

    # ASSERT
    assert fp.calls[0] == conan_install_cmd
    assert fp.calls[1] == conan_build_cmd
    assert len(fp.calls) == 2


def test_scargo_test_run_ut_verbose(
    config: Config,
    mock_get_project_root: None,
    fp: FakeProcess,
) -> None:
    # ARRANGE
    ctest_cmd = ["ctest", "--verbose"]
    html_covarage_cmd = [
        "gcovr",
        "-r",
        "ut",
        ".",
        "--html",
        "ut-coverage.html",
        "--gcov-executable",
        GCOV_EXECUTABLE,
    ]

    fp.register(ctest_cmd)
    fp.register(html_covarage_cmd)

    # ACT
    run_ut(config, True, TEST_BUILD_DIR)

    # ASSERT
    assert fp.calls[0] == ctest_cmd
    assert fp.calls[1] == html_covarage_cmd
    assert len(fp.calls) == 2


def test_scargo_test_run_it_verbose(
    config: Config,
    mock_get_project_root: None,
    fp: FakeProcess,
) -> None:
    # ARRANGE
    ctest_cmd = ["ctest", "--verbose"]
    html_covarage_cmd = [
        "gcovr",
        "-r",
        "it",
        ".",
        "--txt",
        "it-coverage.txt",
        "--html",
        "it-coverage.html",
        "--gcov-executable",
        GCOV_EXECUTABLE,
    ]
    cat_cmd = "cat it-coverage.txt"

    fp.register(ctest_cmd)
    fp.register(html_covarage_cmd)
    fp.register(cat_cmd)

    # ACT
    run_it(config, True)

    # ASSERT
    assert fp.calls[0] == ctest_cmd
    assert fp.calls[1] == html_covarage_cmd
    assert fp.calls[2] == cat_cmd
    assert len(fp.calls) == 3


def test_no_test_dir_fail(
    config: Config,
    mock_get_project_root: None,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # ARRANGE
    monkeypatch.setattr(Path, "exists", lambda _: False)

    # ACT
    with pytest.raises(SystemExit) as error:
        scargo_test(False)

    # ASSERT
    assert "Directory `tests` does not exist." in caplog.text
    assert error.value.code == 1


# def test_no_tests_cmake_file_fail(
#     create_new_project: None, caplog: pytest.LogCaptureFixture, config: Config
# ) -> None:
#     Path("tests/CMakeLists.txt").unlink()
#     with pytest.raises(SystemExit):
#         scargo_test(False)


def test_conan_tests_install_fail(
    config: Config,
    mock_get_project_root: None,
    fp: FakeProcess,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # ARRANGE
    monkeypatch.setattr(Path, "exists", lambda _: True)

    fp.register(
        ["conan", "install", str(TEST_SRC_DIR), "-if", str(TEST_BUILD_DIR)],
        returncode=1,
    )
    fp.register(["conan", "build", str(TEST_SRC_DIR), "-bf", str(TEST_BUILD_DIR)])

    # ACT
    with pytest.raises(SystemExit) as error:
        scargo_test(False)

    # ASSERT
    assert "Failed to build tests." in caplog.text
    assert error.value.code == 1


def test_conan_tests_build_fail(
    config: Config,
    mock_get_project_root: None,
    fp: FakeProcess,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # ARRANGE
    monkeypatch.setattr(Path, "exists", lambda _: True)

    fp.register(["conan", "install", str(TEST_SRC_DIR), "-if", str(TEST_BUILD_DIR)])
    fp.register(
        ["conan", "build", str(TEST_SRC_DIR), "-bf", str(TEST_BUILD_DIR)], returncode=1
    )

    # ACT
    with pytest.raises(SystemExit) as error:
        scargo_test(False)

    # ASSERT
    assert "Failed to build tests." in caplog.text
    assert error.value.code == 1


def test_scargo_test_run_ut_fail(
    config: Config,
    mock_get_project_root: None,
    caplog: pytest.LogCaptureFixture,
    fp: FakeProcess,
) -> None:
    # ARRANGE
    fp.register(["ctest"])
    fp.register(
        [
            "gcovr",
            "-r",
            "ut",
            ".",
            "--html",
            "ut-coverage.html",
            "--gcov-executable",
            GCOV_EXECUTABLE,
        ],
        returncode=1,
    )

    # ACT
    with pytest.raises(SystemExit) as error:
        run_ut(config, False, TEST_BUILD_DIR)

    # ASSERT
    assert "Fail to run project tests" in caplog.text
    assert error.value.code == 1
