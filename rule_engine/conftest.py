import sys
from pathlib import Path

# Automatically add rule_engine directory to sys.path for pytest discovery
rule_engine_dir = Path(__file__).resolve().parent
if str(rule_engine_dir) not in sys.path:
    sys.path.insert(0, str(rule_engine_dir))
