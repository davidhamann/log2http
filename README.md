# log2http

log2http watches log files and sends new contents to a specified http endpoint. That's it.

## Install

You will need Python >= 3.6.

Install the application like this (preferably in a [virtualenv](https://virtualenv.pypa.io/en/stable/)):

`pip install log2http`

## Setup

Place a YAML config file like the following at a location of your preference:

```
-
  logfile: /Users/demo/example.log
  endpoint: http://endpoint1.example.com/tag/sample
  min_lines: 5
-
  logfile: /var/log/system.log
  endpoint: http://endpoint2.example.com/tag/syslog
  min_lines: 2
```

- `logfile` specifies the file to watch
- `endpoint` is the http endpoint you want to send the collected log lines to (as POST). Usually, this will be the url of a logging service, e.g. `http://logs-01.loggly.com/bulk/token/tag/example/`
- `min_lines` sets the minimum of lines that must be collected until a http request is made (use this to minimize http overhead per logged event)

## Usage

Once installed, you can launch log2http from your terminal:

`log2http --config=/path/to/the/config.yml`

When log2http is running, create some sample events to see if they are being collected. For example in bash:

`for i in {1..6}; do echo "hello world" >> example.log; done`

The output should tell you if events are being collected and sent.

You could also start the log collector from Python like this:

```
from log2http import load_config, LogCollector

config = load_config('/your/path/to/config.yml')
collector = LogCollector(config)
with collector:
    collector.start() # will run until interrupted
```

## Local development

See `requirements-dev.txt` for development requirements.

Run tests with `pytest`.

Run static type checking with `mypy --ignore-missing-imports log2http`.
