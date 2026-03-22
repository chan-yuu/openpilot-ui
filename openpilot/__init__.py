"""
Openpilot UI - Standalone UI package extracted from openpilot.

This package contains:
- cereal: Messaging definitions and infrastructure
- msgq: Message queue and VisionIpc
- common: Common utilities and transformations
- system: System UI components
- selfdrive: Main UI application and mock data
- tools: Utilities and launch scripts
"""

import os
import sys
from pathlib import Path

# Set BASEDIR to the package root
BASEDIR = Path(__file__).parent.resolve()

# Ensure the package root is in sys.path
if str(BASEDIR) not in sys.path:
    sys.path.insert(0, str(BASEDIR))

__version__ = "0.1.0"