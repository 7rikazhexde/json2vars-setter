"""
Common pytest fixtures and test settings
"""

import sys
from pathlib import Path

# Add project root directory to path (needed for relative import)
_project_root: Path = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))
