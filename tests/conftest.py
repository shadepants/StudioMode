
import sys
from unittest.mock import MagicMock

# Mock dependencies that might not be installed
if 'httpx' not in sys.modules:
    sys.modules['httpx'] = MagicMock()

if 'litellm' not in sys.modules:
    sys.modules['litellm'] = MagicMock()
