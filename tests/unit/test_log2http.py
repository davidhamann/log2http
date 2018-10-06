import unittest
import os
import tempfile
import mock
import requests
from log2http import load_config, LogCollector

class Log2HttpTestCase(unittest.TestCase):
    '''log2http test suite'''

    def setUp(self) -> None:
        '''Prepare test environment'''

        # get path of sample yml config to test config loader
        self.sample_yml_config = os.path.join(os.path.dirname(__file__), 'sample_config.yml')

        # prepare fake config dict with temp file
        self.fake_log = tempfile.NamedTemporaryFile(mode="a+", prefix='log2http_', delete=False)
        self.fake_config = [{
            'endpoint': 'http://127.0.0.1/fake/',
            'min_lines': 3,
            'logfile': self.fake_log.name
        }]

    def tearDown(self):
        '''Close and remove temp file'''
        logfile = self.fake_log.name
        self.fake_log.close()
        os.remove(logfile)

    def test_config_loader(self) -> None:
        '''Test yml config loading'''
        config = load_config(self.sample_yml_config)

        # test that loaded yml config file contains exactly 2 entries
        self.assertEqual(len(config), 2)

        # test that config contains specified keys
        self.assertEqual(config[0].keys(), set(('logfile', 'endpoint', 'min_lines')))

    def test_fail_on_invalid_config(self) -> None:
        '''Test that an empty/invalid config raises a ValueError'''
        empty_config = []
        incomplete_config = [{'logfile': '/var/log/system.log'}]

        with self.assertRaises(ValueError):
            LogCollector(empty_config)

        with self.assertRaises(ValueError):
            LogCollector(incomplete_config)

    # FIXME: basic test for LogCollector. Still missing tests for other methods.
    @mock.patch.object(requests, 'post')
    def test_collect(self, mock_post) -> None:
        '''Test collecting new lines'''
        mock_response = mock.Mock()
        mock_post.return_value = mock_response
        mock_response.status_code = 200

        sample_events = ['Oct  6 18:41:53 Sample event\n', 'Oct  6 19:01:36 Another one\n']
        with LogCollector(self.fake_config) as collector:
            collector.open()
            self.fake_log.write(''.join(sample_events))
            self.fake_log.flush()
            collector.collect()

            self.assertEqual(collector.lines[0], sample_events)
