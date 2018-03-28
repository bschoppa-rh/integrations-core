# (C) Datadog, Inc. 2010-2018
# All rights reserved
# Licensed under Simplified BSD License (see LICENSE)

import pytest
import os
import subprocess


HERE = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="session")
def spin_up_apache():
    env = os.environ
    env['APACHE_CONFIG'] = os.path.join(HERE, 'config', 'httpd.conf')
    args = [
        "docker-compose",
        "-f", os.path.join(HERE, 'compose', 'standalone.compose')
    ]
    subprocess.check_call(args + ["up", "-d"], env=env)
    yield
    subprocess.check_call(args + ["down"], env=env)
