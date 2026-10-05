#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded offline RandomX comparison; never submits a benchmark or pool share."""
import argparse
import datetime
import json
import os
from pathlib import Path
import platform
import re
import signal
import statistics
import subprocess
import tempfile
import time

# XMRig 6.26.0 src/backend/common/benchmark/BenchState_test.h.
# The single-thread benchmark uses a different nonce schedule.
REFERENCE = {
    "rx/0": {
        "250K": ("90A15B799486F3EB", "7D6054757BB08A63"),
        "1M": ("3DF47B0A427C93D9", "898B6E0431C28A6B"),
    },
    "rx/2": {
        "250K": ("F83B6D9D355EE5B1", "18CF741A71484072"),
        "1M": ("9E16F7CB56B366E1", "88D6B8FB70CD479D"),
    },
}
FINISHED = re.compile(r"benchmark finished in ([0-9.]+) seconds \(([0-9.]+) h/s\).*hash sum = ([0-9A-Fa-f]{16})")
READY = re.compile(r"READY threads (\d+)/(\d+)")


def benchmark(binary, mode, algo, args, output, run_id):
    log_path = output / (run_id + ".log")
    config = {
        "autosave": False, "background": False, "colors": False,
        "title": False, "watch": False, "pools": [],
        "benchmark": {"size": args.size, "algo": algo, "submit": False},
        "randomx": {"wrmsr": False, "rdmsr": True, "1gb-pages": False,
                    "init": args.threads, "numa": True, "scratchpad_prefetch_mode": args.prefetch},
        "cpu": {"enabled": True, "huge-pages": args.huge_pages,
                "huge-pages-jit": False, "yield": not args.no_yield,
                "*": {"intensity": 1, "threads": args.threads, "affinity": -1}},
        "opencl": {"enabled": False}, "cuda": {"enabled": False},
    }
    if mode is not None:
        config["randomx"]["aes"] = mode
    with tempfile.TemporaryDirectory(prefix="metaxmrig-bench-") as tmp:
        config_path = output / (run_id + ".config.json")
        config_path.write_text(json.dumps(config), encoding="utf-8")
        # CLI --bench replaces the whole CPU object and changes yield/JIT.
        # Keep benchmark and all nested settings in one JSON document.
        cmd = [str(binary), "-c", str(config_path), "--no-color", "--no-title",
               "--log-file=" + str(log_path)]
        print(f"{run_id}: starting {algo}, {args.threads} threads", flush=True)
        # XMRig disables its console logger when stdout is a regular file.
        # Use its own file logger; keep startup errors in a separate file.
        with (output / (run_id + ".stdout.log")).open("w", encoding="utf-8") as log:
            proc = subprocess.Popen(cmd, cwd=tmp, stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + args.timeout
                while True:
                    contents = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
                    ready = READY.search(contents)
                    if ready and (int(ready[1]) != args.threads or int(ready[2]) != args.threads):
                        raise RuntimeError(f"requested threads did not become ready: {log_path}")
                    match = FINISHED.search(contents)
                    if match:
                        break
                    if proc.poll() is not None:
                        raise RuntimeError(f"miner exited before completing: {log_path}")
                    if time.monotonic() >= deadline:
                        raise RuntimeError(f"benchmark timed out after {args.timeout}s: {log_path}")
                    time.sleep(0.25)
            finally:
                if proc.poll() is None:
                    proc.send_signal(signal.SIGINT)
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
    ready = READY.search(contents)
    if not ready or int(ready[1]) != args.threads or int(ready[2]) != args.threads:
        raise RuntimeError(f"requested threads did not become ready: {log_path}")
    expected = REFERENCE[algo][args.size][args.threads > 1]
    checksum = match[3].upper()
    if checksum != expected:
        raise RuntimeError(f"WRONG HASH: {checksum}, expected {expected}: {log_path}")
    selected = re.search(r"AES implementation: (\S+) \(requested: (\S+)\)", contents)
    result = {
        "run": run_id, "binary": str(binary), "mode": mode or "upstream",
        "algorithm": algo, "seconds": float(match[1]), "hashrate": float(match[2]),
        "checksum": checksum, "expected": expected, "correct": True,
        "selected_aes": selected[1] if selected else "upstream dispatch",
        "memory_status": [line for line in contents.splitlines() if "huge pages" in line],
        "log": log_path.name,
    }
    print(f"{run_id}: {result['hashrate']:.1f} H/s, checksum OK, AES={result['selected_aes']}", flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=Path("./metaxmrig"))
    parser.add_argument("--baseline", type=Path, default=Path("./xmrig-baseline"))
    parser.add_argument("--skip-baseline", action="store_true")
    parser.add_argument("--modes", nargs="+", choices=["auto", "aes", "vaes512"], default=["aes", "vaes512"])
    parser.add_argument("--algorithms", nargs="+", choices=list(REFERENCE), default=["rx/0"])
    parser.add_argument("--threads", type=int, default=min(4, len(os.sched_getaffinity(0))))
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--size", choices=["250K", "1M"], default="250K")
    parser.add_argument("--prefetch", type=int, choices=range(4), default=1)
    parser.add_argument("--no-yield", action="store_true")
    parser.add_argument("--huge-pages", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--output", type=Path, default=Path("benchmark-results"))
    args = parser.parse_args()
    if min(args.threads, args.rounds, args.timeout) < 1:
        parser.error("threads, rounds and timeout must be positive")
    candidate = args.candidate.resolve()
    cases = [(mode, candidate) for mode in dict.fromkeys(args.modes)]
    if not args.skip_baseline:
        cases.insert(0, (None, args.baseline.resolve()))
    for _, binary in cases:
        if not binary.is_file() or not os.access(binary, os.X_OK):
            parser.error(f"executable not found: {binary}")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if (output / "results.json").exists():
        parser.error("output already contains results.json; choose a new output directory")
    machine = {"platform": platform.platform(), "allowed_cpus": sorted(os.sched_getaffinity(0))}
    try:
        machine["lscpu"] = subprocess.check_output(["lscpu", "--json"], text=True)
    except (OSError, subprocess.CalledProcessError):
        pass
    report = {
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "machine": machine, "settings": {
            "threads": args.threads, "size": args.size, "rounds": args.rounds,
            "prefetch": args.prefetch, "yield": not args.no_yield,
            "huge_pages_requested": args.huge_pages, "msr_writes": False,
        }, "runs": [], "summary": [],
    }
    try:
        for algo in args.algorithms:
            for round_index in range(args.rounds):
                # Rotate run order so one implementation is not always first.
                offset = round_index % len(cases)
                ordered = cases[offset:] + cases[:offset]
                for mode, binary in ordered:
                    run_id = f"{algo.replace('/', '-')}-{mode or 'upstream'}-{round_index + 1}"
                    report["runs"].append(benchmark(binary, mode, algo, args, output, run_id))
                    (output / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        for algo in args.algorithms:
            baseline = [r["hashrate"] for r in report["runs"] if r["algorithm"] == algo and r["mode"] == "upstream"]
            for mode, _ in cases:
                values = [r["hashrate"] for r in report["runs"] if r["algorithm"] == algo and r["mode"] == (mode or "upstream")]
                median = statistics.median(values)
                row = {"algorithm": algo, "mode": mode or "upstream", "median_hs": median,
                       "min_hs": min(values), "max_hs": max(values)}
                if baseline:
                    row["vs_upstream_percent"] = (median / statistics.median(baseline) - 1) * 100
                report["summary"].append(row)
                print(json.dumps(row), flush=True)
    except (RuntimeError, KeyboardInterrupt) as error:
        report["error"] = str(error) or "interrupted"
        (output / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        raise SystemExit(report["error"])
    (output / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Results: {output / 'results.json'}")


if __name__ == "__main__":
    main()
