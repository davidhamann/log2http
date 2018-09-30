'''
log2http

Usage:
  log2http
  log2http [--config=/path/to/log2http.yml]
  log2http -h | --help
  log2http --version

Options:
  -h --help                         Show this help
  --version                         Show version
  --config=<path>                   Path to YAML config file

Example:
  log2http --config=/etc/log2http.yml

Help:
  https://github.com/davidhamann/log2http
'''

import os
import sys
import time
from typing import List, IO, Tuple, Optional
from pathlib import Path
from mypy_extensions import TypedDict
from docopt import docopt
import requests
import yaml
from .const import __version__

class Config(TypedDict):
    '''Define typing for config'''
    logfile: str
    endpoint: str
    min_lines: int

class LogCollector(object):
    def __init__(self, config: List[Config]) -> None:
        self.config = config

        # stores file objects and collected lines per file
        self._files: List[Tuple[IO, List[str]]] = []

        # validate config
        for entry in self.config:
            if entry.keys() != set(('endpoint', 'logfile', 'min_lines')):
                raise ValueError('Config contains invalid or incomplete keys')

    def send(self, file_idx: int) -> None:
        '''Sends collected log lines to http endpoint specified in config.'''
        data = '\n'.join(self._files[file_idx][1])
        res = requests.post(self.config[file_idx]["endpoint"], data=data)
        print(f'sending to http endpoint {self.config[file_idx]["endpoint"]} now.')
        #print(res.text)

    def open(self) -> None:
        '''opens files to watch and adds them to _files.'''
        for entry in self.config:
            f = open(entry['logfile'])

            # seek to end so that we only collect new lines from now
            f.seek(0, os.SEEK_END)
            self._files.append((f, []))

    def reset_lines(self, file_idx: int) -> None:
        '''Resets the collected lines for the specified file index.'''
        self._files[file_idx][1].clear()

    def collect(self, interval: int = 1) -> None:
        '''Starts collection loop.

        Starts watching files specified in config and runs indefinitely to collect and send
        data added to those files.

        Parameters
        ----------
        interval : int
            Collection interval in seconds in which to check for file additions.
            Value is used to time.sleep() in between the runs.

        '''

        self.open() # open files to watch

        while True:
            for i, logfile in enumerate(self._files):
                lines = logfile[0].readlines()
                if lines:
                    self._files[i][1].extend(lines)
                    collected = self._files[i][1]
                    print(f"collected {collected}")
                    if len(collected) > self.config[i]['min_lines']:
                        self.send(i)
                        self.reset_lines(i)

                time.sleep(interval)

def main() -> None:
    '''CLI entry point'''
    options = docopt(__doc__, version=__version__)

    # load config from argument or defaut location
    config_path = options['--config']
    config = load_config(config_path)

    if config:
        # start collection loop with settings in config
        collector = LogCollector(config)
        collector.collect()
    else:
        sys.exit('Could not find configuration file. Please specify via --config.')

def load_config(path: str = None) -> Optional[List]:
    '''Loads yaml config from given path or default location.'''
    if not path:
        path = '/etc/log2http.yml'

    config_file = Path(path)
    if not config_file.is_file():
        return None

    with open(path) as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            #FIXME: handle exception
            raise exc

    return config
