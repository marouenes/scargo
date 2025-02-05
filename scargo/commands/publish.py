# #
# @copyright Copyright (C) 2023 SpyroSoft Solutions S.A. All rights reserved.
# #


"""Publish conan package into repository"""
import subprocess
import sys
from pathlib import Path

from scargo.conan_utils import conan_add_remote, conan_source
from scargo.config_utils import prepare_config
from scargo.logger import get_logger

logger = get_logger()


def scargo_publish(repo: str, profile: str = "Release") -> None:
    """
    Publish conan package

    :param str repo: repository name
    :return: None
    """
    config = prepare_config()
    project_path = config.project_root
    project_config = config.project
    project_name = project_config.name

    build_dir = Path(project_path, "build", profile)

    if not build_dir.exists():
        logger.error("Build folder for specified build type does not exist")
        logger.info(f"Did you run 'scargo build --profile {profile}'?")
        sys.exit(1)

    conan_add_remote(project_path, config)
    conan_source(project_path)

    # Export package
    try:
        subprocess.run(
            [
                "conan",
                "export-pkg",
                ".",
                "-pr",
                f"./config/conan/profiles/{config.project.target.family}_{profile}",
                "-of",
                build_dir,
            ],
            check=True,
            cwd=project_path,
        )
    except subprocess.CalledProcessError:
        logger.error("Unable to export package")
        sys.exit(1)

    # Test if package has been exported successfully
    try:
        subprocess.run(
            [
                "conan",
                "test",
                "test_package",
                f"{project_name}/{config.project.version}",
                "-pr",
                f"./config/conan/profiles/{config.project.target.family}_{profile}",
            ],
            check=True,
            cwd=project_path,
        )
    except subprocess.CalledProcessError:
        logger.error("Package test failed")
        sys.exit(1)

    # Upload package to conan remote
    conan_repo = ["-r", repo] if repo else []
    try:
        subprocess.run(
            [
                "conan",
                "upload",
                f"{project_name}",
                *conan_repo,
                "--confirm",
            ],
            check=True,
            cwd=project_path,
        )
    except subprocess.CalledProcessError:
        logger.error("Unable to publish package")
        sys.exit(1)
