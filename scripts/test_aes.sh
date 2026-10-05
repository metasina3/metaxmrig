#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
out=${1:-"$root/build-aes-test"}
mkdir -p "$out"
compiler=${CXX:-g++}
common=(-std=c++11 -Ofast -ffunction-sections -fdata-sections -DNDEBUG -I "$root/src" -I "$root/src/3rdparty")
# Generic reference is intentionally compiled without XMRIG_VAES dispatch.
"$compiler" "${common[@]}" -maes -c "$root/src/crypto/randomx/aes_hash.cpp" -o "$out/aes128.o"
"$compiler" "${common[@]}" -mavx512f -mvaes -c "$root/src/crypto/randomx/aes_hash_vaes512.cpp" -o "$out/vaes512.o"
"$compiler" "${common[@]}" -c "$root/tests/meta_aes_probe.cpp" -o "$out/probe.o"
"$compiler" -Wl,--gc-sections "$out/probe.o" "$out/aes128.o" "$out/vaes512.o" -pthread -o "$out/aes-probe"
set +e
"$out/aes-probe" > "$out/results.json"
status=$?
set -e
if [ "$status" -eq 77 ]; then
    cat "$out/results.json"
    echo 'SKIP: this CPU cannot execute the VAES512 kernel'
    exit 0
fi
cat "$out/results.json"
exit "$status"
