"""Bounded Linux runner subprocess operation; never release a lease on timeout."""
import os
import signal
import subprocess
import time

def run_operation(argv, deadline, *, cwd=None, env=None, grace=10):
    if os.name != "posix":
        raise RuntimeError("POSIX process-group adapter required")
    if not 0 < grace <= 30:
        raise ValueError("invalid cleanup grace")
    remaining = deadline - time.monotonic() - grace
    if remaining <= 0:
        raise TimeoutError("insufficient operation budget")
    p = subprocess.Popen(argv, cwd=cwd, env=env, start_new_session=True)
    try:
        code = p.wait(timeout=remaining)
    except BaseException:
        try:
            os.killpg(p.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            p.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            pass
        finally:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.wait()
        raise
    if code:
        raise subprocess.CalledProcessError(code, argv)
    return code
