# #
# @copyright Copyright (C) 2023 SpyroSoft Solutions S.A. All rights reserved.
# #

from scargo.config import Config
from scargo.jinja.base_gen import create_file_from_template


def generate_cmake(config: Config) -> None:
    create_file_from_template(
        "templates/CMakeLists.txt.j2",
        "CMakeLists.txt",
        template_params={"config": config},
        config=config,
    )
