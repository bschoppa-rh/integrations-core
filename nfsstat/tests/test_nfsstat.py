# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import os

import mock
import pytest
from datadog_checks.stubs import aggregator as _aggregator

from datadog_checks.nfsstat import NfsStatCheck

metrics = [
    'system.nfs.ops',
    'system.nfs.rpc_bklog',
    'system.nfs.read_per_op',
    'system.nfs.read.ops',
    'system.nfs.read_per_s',
    'system.nfs.read.retrans',
    'system.nfs.read.retrans.pct',
    'system.nfs.read.rtt',
    'system.nfs.read.exe',
    'system.nfs.write_per_op',
    'system.nfs.write.ops',
    'system.nfs.write_per_s',
    'system.nfs.write.retrans',
    'system.nfs.write.retrans.pct',
    'system.nfs.write.rtt',
    'system.nfs.write.exe',
]

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')


@pytest.fixture
def aggregator():
    _aggregator.reset()
    return _aggregator


class TestNfsstat:
    CHECK_NAME = 'nfsstat'
    INSTANCES = {
        'main': {
            'stats_url': 'http://localhost:80/stats',
        },
    }

    INIT_CONFIG = {
        'nfsiostat_path': '/opt/datadog-agent/embedded/sbin/nfsiostat',
    }

    def test_check(self, aggregator):
        instance = self.INSTANCES['main']
        c = NfsStatCheck(self.CHECK_NAME, self.INIT_CONFIG, {}, [instance])

        with open(os.path.join(FIXTURE_DIR, 'nfsiostat'), 'rb') as f:
            mock_output = f.read()

        with mock.patch('datadog_checks.nfsstat.nfsstat.get_subprocess_output',
                        return_value=(mock_output, '', 0)):
            c.check(instance)

        nfs_server_tag = 'nfs_server:192.168.34.1'
        nfs_export_tag = 'nfs_export:/exports/nfs/datadog/{0}'
        nfs_mount_tag = 'nfs_mount:/mnt/datadog/{0}'

        folder_names = ['two']

        for metric in metrics:
            for folder in folder_names:
                tags = [
                    'optional:tag1',
                    nfs_server_tag,
                    nfs_export_tag.format(folder),
                    nfs_mount_tag.format(folder)
                ]
                aggregator.assert_metric(metric, tags=tags)

        assert aggregator.metrics_asserted_pct == 100.0
