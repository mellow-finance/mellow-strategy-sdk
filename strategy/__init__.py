import os
import sys
import structlog

if os.path.split(os.getcwd())[0] not in sys.path:
    sys.path.append(os.path.split(os.getcwd())[0])

log = structlog.get_logger()
