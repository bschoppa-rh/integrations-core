# (C) Datadog, Inc. 2010-2018
# All rights reserved
# Licensed under Simplified BSD License (see LICENSE)

import pytest
import os
import subprocess

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
BAD_CONFIG = [
    {
        'apache_status_url': 'http://localhost:1234/server-status',
    }
]

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
        "-f", os.path.join(HERE, 'compose', 'standalone.compose')
    ]
    subprocess.check_call(args + ["up", "-d"], env=env)
    yield
    subprocess.check_call(args + ["down"], env=env)


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
            aggregator.assert_metric(mname, tags=tags, count=1)
        assert aggregator.service_checks('apache.can_connect')[0].status == Apache.OK

        sc_tags = ['host:localhost', 'port:8180'] + tags
        for tag in aggregator.service_checks('apache.can_connect')[0].tags:
            assert tag in sc_tags


# def test_check(self):
#     config = {
#         'instances': self.CONFIG_STUBS
#     }
#
#     self.run_check_twice(config)
#
#     # Assert metrics
#     for stub in self.CONFIG_STUBS:
#         expected_tags = stub['tags']
#
#         for mname in self.APACHE_GAUGES + self.APACHE_RATES:
#             self.assertMetric(mname, tags=expected_tags, count=1)
#
#         # Assert service checks
#         self.assertServiceCheck('apache.can_connect', status=AgentCheck.OK,
#                             tags=['host:localhost', 'port:8180'] + expected_tags, count=1)
#
#     self.coverage_report()
#
#
# def test_connection_failure(self):
#     config = {
#         'instances': self.BAD_CONFIG
#     }
#
#     # Assert service check
#     self.assertRaises(
#         Exception,
#         lambda: self.run_check(config)
#     )
#     self.assertServiceCheck('apache.can_connect', status=AgentCheck.CRITICAL,
#                             tags=['host:localhost', 'port:1234'], count=1)
#
#     self.coverage_report()
