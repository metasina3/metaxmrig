#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Integration check: CLI AES override preserves the existing RandomX config."""
import json
from pathlib import Path
import signal
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

binary = Path(sys.argv[1]).resolve()
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
for override, expected in [(None, "aes"), ("vaes512", "vaes512"), ("invalid", "auto")]:
    with tempfile.TemporaryDirectory(prefix="meta-config-test-") as tmp, socket.socket() as pool:
        tmp = Path(tmp)
        # An inert local pool keeps the miner idle; no dataset or hashes start.
        pool.bind(("127.0.0.1", 0))
        pool.listen(1)
        pool_port = pool.getsockname()[1]
        token = secrets.token_hex(16)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        rx = {"aes": "aes", "mode": "fast", "init": 2, "init-avx2": 0,
              "wrmsr": False, "rdmsr": False, "numa": False,
              "1gb-pages": False, "scratchpad_prefetch_mode": 2}
        config = {"autosave": False, "watch": False, "colors": False,
                  "http": {"enabled": True, "host": "127.0.0.1", "port": port,
                           "restricted": False, "access-token": token},
                  "cpu": {"enabled": False, "hw-aes": False},
                  "randomx": rx, "pools": [{"url": f"127.0.0.1:{pool_port}", "user": "config-test"}]}
        path = tmp / "config.json"
        path.write_text(json.dumps(config))
        cmd = [str(binary), "-c", str(path), "--log-file=" + str(tmp / "miner.log")]
        if override is not None:
            cmd.append("--randomx-aes=" + override)
        proc = subprocess.Popen(cmd, cwd=tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            deadline = time.monotonic() + 15
            while True:
                try:
                    request = urllib.request.Request(f"http://127.0.0.1:{port}/2/config", headers={"Authorization": "Bearer " + token})
                    with opener.open(request, timeout=1) as response:
                        actual = json.load(response)
                    break
                except (urllib.error.URLError, TimeoutError):
                    if proc.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError("API did not start: " + (tmp / "miner.log").read_text())
                    time.sleep(0.1)
            assert actual["randomx"]["aes"] == expected, actual["randomx"]
            for key, value in rx.items():
                if key != "aes":
                    assert actual["randomx"][key] == value, (key, actual["randomx"])
            assert actual["cpu"]["enabled"] is False
            assert actual["cpu"]["hw-aes"] is False
            print(f"OK: CLI {override!r} -> AES {expected}; all other RandomX settings preserved")
        finally:
            if proc.poll() is None:
                proc.send_signal(signal.SIGINT)
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
