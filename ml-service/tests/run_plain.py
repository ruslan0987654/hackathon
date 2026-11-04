"""pytest olmadan sadə işə salma: python -m tests.run_plain"""
import importlib
import sys
import time
import traceback

failed = 0
mod = importlib.import_module("tests.test_services")
for name in sorted(n for n in dir(mod) if n.startswith("test_")):
    t = time.time()
    try:
        getattr(mod, name)()
        print(f"PASS {name} ({time.time()-t:.1f}s)")
    except Exception:
        failed += 1
        print(f"FAIL {name}")
        traceback.print_exc()
sys.exit(1 if failed else 0)
