# (C) Datadog, Inc. 2010-2018
# All rights reserved
# Licensed under Simplified BSD License (see LICENSE)

import pytest
import os
import subprocess
import requests

from datadog_checks.apache import Apache

CHECK_NAME = 'apache'

CONFIG_STUBS = [
    {
        'apache_status_url': 'http://localhost:8180/server-status',
        'tags': ['instance:first']
    },
    {
        'apache_status_url': 'http://localhost:8180/server-status?auto',
        'tags': ['instance:second']
    },
]
BAD_CONFIG = {
        'apache_status_url': 'http://localhost:1234/server-status',
}

APACHE_GAUGES = [
    'apache.performance.idle_workers',
    'apache.performance.busy_workers',
    'apache.performance.cpu_load',
    'apache.performance.uptime',
    'apache.net.bytes',
    'apache.net.hits',
    'apache.conns_total',
    'apache.conns_async_writing',
    'apache.conns_async_keep_alive',
    'apache.conns_async_closing'
]

APACHE_RATES = [
    'apache.net.bytes_per_s',
    'apache.net.request_per_s'
]


HERE = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="session")
def spin_up_apache():
    env = os.environ
    env['APACHE_CONFIG'] = os.path.join(HERE, 'config', 'httpd.conf')
    args = [
        "docker-compose",
        "-f", os.path.join(HERE, 'compose', 'apache.yaml')
    ]
    subprocess.check_call(args + ["down"], env=env)
    subprocess.check_call(args + ["up", "-d"], env=env)
    for _ in xrange(0, 100):
        requests.get('http://localhost:8180')
    yield
    # subprocess.check_call(args + ["down"], env=env)


@pytest.fixture
def aggregator():
    from datadog_checks.stubs import aggregator
    aggregator.reset()
    return aggregator


def test_check(aggregator, spin_up_apache):
    apache_check = Apache('redisdb', {}, {})
    for config in CONFIG_STUBS:
        # run twice to pick up rates
        apache_check.check(config)
        apache_check.check(config)

        tags = config['tags']
        for mname in APACHE_GAUGES + APACHE_RATES:
            aggregator.assert_metric(mname, tags=tags, count=2)
        assert aggregator.service_checks('apache.can_connect')[0].status == Apache.OK

        print aggregator.service_checks('apache.can_connect')

        sc_tags = ['host:localhost', 'port:8180'] + tags
        for sc in aggregator.service_checks('apache.can_connect'):
            for tag in sc.tags:
                assert tag in sc_tags

        assert aggregator.metrics_asserted_pct == 100.0
        aggregator.reset()


def test_connection_failure(aggregator, spin_up_apache):
    apache_check = Apache('redisdb', {}, {})
    with pytest.raises(Exception):
        apache_check.check(BAD_CONFIG)

    assert aggregator.service_checks('apache.can_connect')[0].status == Apache.CRITICAL
    assert len(aggregator._metrics) == 0
