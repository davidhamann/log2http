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
import signal
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
        self.interrupt = False

        # stores file objects and collected lines per file
        self._files: List[Tuple[IO, List[str]]] = []

        # validate config
        if not config:
            raise ValueError('Config contains no files to watch')

        for entry in self.config:
            if entry.keys() != set(('endpoint', 'logfile', 'min_lines')):
                raise ValueError('Config contains invalid or incomplete keys')

    def __enter__(self) -> 'LogCollector':
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def send(self, file_idx: int) -> None:
        '''Sends collected log lines to http endpoint specified in config.'''
        data = ''.join(self._files[file_idx][1])

        res = requests.post(self.config[file_idx]["endpoint"], data=data)
        if res.status_code == 200:
            self.reset_lines(file_idx)
            print(f'Sent to http endpoint {self.config[file_idx]["endpoint"]}.')
        else:
            print(f'Sending failed; keeping contents. Response {res.text}')

    def open(self) -> None:
        '''opens files to watch and adds them to _files.'''
        for entry in self.config:
            logfile = open(entry['logfile'])

            # seek to end so that we only collect new lines from now
            logfile.seek(0, os.SEEK_END)
            self._files.append((logfile, []))

    def close(self) -> None:
        '''closes files in _files and sends lines collected (and not sent) so far'''
        for i, logfile in enumerate(self._files):
            logfile[0].close()
            collected = self._files[i][1]
            if collected:
                # indepentend of min_lines, send everything colllected but not sent yet
                self.send(i)

    def reset_lines(self, file_idx: int) -> None:
        '''Resets the collected lines for the specified file index.'''
        self._files[file_idx][1].clear()

    def collect(self) -> None:
        '''Reads in new lines from log files.'''
        for i, logfile in enumerate(self._files):
            lines = logfile[0].readlines()
            if lines:
                # we've read in one or more new lines for this file. Now we need to check if the
                # last line of this read is actually a complete log line (i.e. ends with a newline
                # char). If logs are written in chunks, this prevents individual chunks of the same
                # line to be seen as separate events (for example for the min_lines counter).
                while lines[-1][-1] != '\n' and not self.interrupt:
                    # wait until newline character is written.
                    # keep incomplete line when user interrupts the program, though.
                    more = logfile[0].readline()
                    if not more:
                        time.sleep(.1)
                    else:
                        lines[-1] += more

                self._files[i][1].extend(lines)
                collected = self._files[i][1]
                print(f"collected {len(lines)} new events from {logfile[0].name}")
                if len(collected) >= self.config[i]['min_lines']:
                    self.send(i)

    def start(self, interval: int = 1) -> None:
        '''Starts collection loop.

        Starts watching files specified in config and runs until interrupted to collect and send
        data added to those files. Breaks on SIGINT.

        Parameters
        ----------
        interval : int
            Collection interval in seconds in which to check for file additions.
            Value is used to time.sleep() in between the runs.
        '''

        self.open() # open files to watch

        # setup SIGINT handler
        # signal handler gets signal and frame. Wrap in lambda to be able to use
        # own signal handler as class method expecting self
        signal.signal(signal.SIGINT, lambda signal, frame: self._signal_handler())

        while True: # continue to collect and send new lines
            self.collect()
            time.sleep(interval)

            if self.interrupt:
                break

    @property
    def lines(self):
        return [f[1] for f in self._files]

    def _signal_handler(self) -> None:
        '''Will handle interrupt signal to interrupt collector loop'''
        print('Stopping...')
        self.interrupt = True

def main() -> None:
    '''CLI entry point'''
    options = docopt(__doc__, version=__version__)

    # load config from argument or defaut location
    config_path = options['--config']
    config = load_config(config_path)

    if config:
        # start collection loop with settings in config
        collector = LogCollector(config)
        with collector:
            collector.start()
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
