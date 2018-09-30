"""log2http watches log files and sends new contents to a specified http endpoint."""

from .const import __version__
from .app import LogCollector, load_config
