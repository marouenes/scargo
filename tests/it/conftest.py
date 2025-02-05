import os
import re
import subprocess
from pathlib import Path

import pytest

from scargo.global_values import SCARGO_PKG_PATH


@pytest.fixture()
def create_tmp_directory(tmp_path: Path) -> None:
    os.chdir(tmp_path)


@pytest.fixture(scope="session")
def use_local_scargo() -> None:
    # This is necessary, so we can test latest changes in docker
    # Might be worth to rework with devpi later on
    scargo_repo_root = SCARGO_PKG_PATH.parent
    scargo_docker_env_name = "SCARGO_DOCKER_INSTALL_LOCAL"

    # If tests are run locally, wheel should be always rebuild to avoid using obsolete version
    # In case of running on CI, many workers should use the same version created earlier in workflow
    if "CI" in os.environ:
        if scargo_docker_env_name in os.environ:
            return
        else:
            raise KeyError(f"{scargo_docker_env_name} not found in the env variables")

    result = subprocess.run(
        ["flit", "build"],
        cwd=scargo_repo_root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    match = re.search(r"Built\swheel:\s*(dist/scargo.*.whl)", result.stdout)
    assert match
    os.environ[scargo_docker_env_name] = match.group(1)
