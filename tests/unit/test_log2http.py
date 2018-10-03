import unittest
import os
import tempfile
import time
import threading
from docopt import docopt
from log2http import load_config, LogCollector

class Log2HttpTestCase(unittest.TestCase):
    """log2http test suite"""

    def setUp(self) -> None:
        """Prepare test environment"""

        # get path of sample yml config to test config loader
        self.sample_yml_config = os.path.join(os.path.dirname(__file__), 'sample_config.yml')

        # prepare fake config dict to use on temp file
        self.fake_config = [{
            'endpoint': 'http://111.111.111.111/fake/',
            'min_lines': 1
        }]

    def test_config_loader(self) -> None:
        """Test yml config loading"""
        config = load_config(self.sample_yml_config)

        # test that loaded yml config file contains exactly 2 entries
        self.assertEqual(len(config), 2)

        # test that config contains specified keys
        self.assertEqual(config[0].keys(), set(('logfile', 'endpoint', 'min_lines')))

    def test_fail_on_invalid_config(self) -> None:
        """Test that an empty/invalid config raises a ValueError"""
        empty_config = []
        incomplete_config = [{'logfile': '/var/log/system.log'}]

        with self.assertRaises(ValueError):
            LogCollector(empty_config)

        with self.assertRaises(ValueError):
            LogCollector(incomplete_config)

    def test_collect(self) -> None:
        # FIXME: mock http endpoint
        # FIXME: termination signal

        # create temporary file to use as "fake" log file
        with tempfile.NamedTemporaryFile(mode="a+") as fake_log:
            # add fake_log to fake_config, then pass to collector to watch
            self.fake_config[0]['logfile'] = fake_log.name

            # run collector in separate thread so that it is able to watch what we
            # will write into the temp file
            collector_thread = CollectorThread(self.fake_config)
            collector_thread.daemon = True # daemonize to exit entire app when only the thread is left
            collector_thread.start()

            # append to fake log file after short delay
            time.sleep(1)
            fake_log.write("one\ntwo")
            fake_log.flush()

            print('thread id', collector_thread.ident)
            print(fake_log.name)
            collector_thread.join() # FIXME: will never end; handle termination signal event

class CollectorThread(threading.Thread):
    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        collector = LogCollector(self.config)
        collector.collect()
