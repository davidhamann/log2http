CONFIG = [
    {
        'logfile': '/Users/dh/Desktop/example.log',
        'endpoint': 'http://localhost:5000/bulk/token/tag/example',
        'min_lines': 5 # send logs to endpoint once min_lines is reached
    },
    {
        'logfile': '/var/log/system.log',
        'endpoint': 'http://localhost:5000/bulk/token/tag/syslog,macos',
        'min_lines': 2
    }
]

"""
[
    [fileobj, ['line 1', 'line 2']],
    [fileobj, ['some line']]
]
"""

import os
import time

class LogCollector(object):
    def __init__(self, config):
        self.config = config #FIXME: consolidate; use files or config, not both
        self.files = []

    def send(self, file_idx):
        print(f'Would send to http endpoint {self.config[file_idx]["endpoint"]} now.')

    def open(self):
        # open files to watch
        for entry in self.config:
            f = open(entry.get('logfile'))
            f.seek(0, os.SEEK_END)
            self.files.append([f, []])

    def reset_lines(self, file_idx):
        print('Resetting contents...')
        self.files[file_idx][1].clear()

    def collect(self, interval=1):

        self.open() # open files

        while True:
            for i, f in enumerate(self.files):
                lines = f[0].readlines()
                if lines:
                    self.files[i][1] += lines
                    collected = self.files[i][1]
                    print(f"collected {collected}")
                    if len(collected) > self.config[i].get('min_lines'): #FIXME
                        self.send(i)
                        self.reset_lines(i)

                time.sleep(interval)

def main():
    collector = LogCollector(CONFIG)
    collector.collect()

if __name__ == '__main__':
    main()
