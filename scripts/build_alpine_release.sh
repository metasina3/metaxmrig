#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
work=${1:-"$root/build-release"}
mkdir -p "$work"
work=$(cd "$work" && pwd)
jobs=${BUILD_JOBS:-4}
compiler=${CXX:-g++}
upstream=b2ca72480c58d197e18c885d9fc1a0c8d517e60a
version=$(cat "$root/release/VERSION")
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+-meta\.[0-9]+$ ]]
[ "$(uname -s)" = Linux ] && [ -f /etc/alpine-release ]
case "$(uname -m)" in
    x86_64) arch=x64 ;;
    aarch64) arch=arm64 ;;
    *) echo 'Supported build architectures: x86_64, aarch64' >&2; exit 1 ;;
esac
git_repo() { git -c safe.directory="$root" -C "$root" "$@"; }
uv_static=$("$compiler" -print-file-name=libuv.a)
[ -f "$uv_static" ] || { echo 'Install libuv-dev and libuv-static.' >&2; exit 1; }
[ -f /usr/lib/libssl.a ] && [ -f /usr/lib/libcrypto.a ]

# Minimal hwloc retains CPU topology/NUMA without runtime plugin dependencies.
archive="$work/hwloc-2.12.1.tar.gz"
if [ ! -f "$archive" ]; then
    curl -fsSL --retry 2 https://download.open-mpi.org/release/hwloc/v2.12/hwloc-2.12.1.tar.gz -o "$archive"
fi
echo "ffa02c3a308275a9339fbe92add054fac8e9a00cb8fe8c53340094012cb7c633  $archive" | sha256sum -c -
if [ ! -f "$work/deps/lib/libhwloc.a" ]; then
    tar --no-same-owner -xzf "$archive" -C "$work"
    (
        cd "$work/hwloc-2.12.1"
        ./configure --prefix="$work/deps" --disable-shared --enable-static \
            --disable-io --disable-libudev --disable-libxml2 --disable-libnuma --disable-cairo
        make -j "$jobs"
        make install
    )
fi
if ! git_repo cat-file -e "$upstream^{commit}" 2>/dev/null; then
    git_repo fetch --depth=1 origin "$upstream"
fi
mkdir -p "$work/upstream"
git_repo archive "$upstream" | tar --no-same-owner -xf - -C "$work/upstream"
flags=(-DCMAKE_BUILD_TYPE=Release -DBUILD_STATIC=ON -DWITH_HWLOC=ON \
    -DWITH_RANDOMX=ON -DWITH_VAES=ON -DWITH_BENCHMARK=ON -DWITH_TLS=ON \
    -DWITH_OPENCL=OFF -DWITH_CUDA=OFF -DWITH_KAWPOW=OFF -DWITH_GHOSTRIDER=OFF \
    -DUV_LIBRARY="$uv_static" \
    -DOPENSSL_SSL_LIBRARY=/usr/lib/libssl.a -DOPENSSL_CRYPTO_LIBRARY=/usr/lib/libcrypto.a \
    -DHWLOC_INCLUDE_DIR="$work/deps/include" -DHWLOC_LIBRARY="$work/deps/lib/libhwloc.a")
cmake -S "$root" -B "$work/candidate" "${flags[@]}"
cmake --build "$work/candidate" -j "$jobs"
cmake -S "$work/upstream" -B "$work/baseline" "${flags[@]}"
cmake --build "$work/baseline" -j "$jobs"

bundle="metaxmrig-$version-linux-musl-$arch"
dest="$work/$bundle"
mkdir -p "$dest/licenses" "$dest/docs"
cp "$work/candidate/xmrig" "$dest/metaxmrig"
cp "$work/baseline/xmrig" "$dest/xmrig-baseline"
cp "$root/scripts/compare_randomx.py" "$dest/compare_randomx.py"
cp "$root/LICENSE" "$dest/LICENSE"
cp "$root"/docs/{TESTING,CHANGES,VALIDATION,PORTABILITY}_FA.md "$dest/docs/"
cp "$root/release/NOTES.md" "$dest/README.md"
cp "$work/hwloc-2.12.1/COPYING" "$dest/licenses/hwloc.txt"
cp "$root"/release/licenses/*.txt "$dest/licenses/"
python3 - "$root" "$dest" <<'PY'
from pathlib import Path
import shutil
import sys
root, dest = map(Path, sys.argv[1:])
notice = ''
for name in ['aes_hash.cpp', 'aes_hash_vaes512.cpp']:
    notice += name + '\n' + (root / 'src/crypto/randomx' / name).read_text().split('*/', 1)[0] + '*/\n\n'
(dest / 'licenses/randomx.txt').write_text(notice)
for path in (root / 'src/3rdparty').rglob('*'):
    if path.is_file() and path.name.upper().startswith(('LICENSE', 'COPYING', 'NOTICE', 'COPYRIGHT')):
        target = dest / 'licenses/vendored' / path.relative_to(root / 'src/3rdparty')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
PY
{
    echo "MetaXMRig $version"
    echo "Source commit: $(git_repo rev-parse HEAD)"
    echo "Upstream baseline commit: $upstream"
    echo "Architecture: $(uname -m); fully static musl Linux executable"
    echo "Alpine: $(cat /etc/alpine-release)"
    echo "Container image: ${BUILD_IMAGE:-not recorded}"
    echo 'CPU backend; RandomX, hardware AES, JIT, NUMA, TLS and benchmark enabled.'
    echo 'VAES512 compiled only on x86-64 and selected only on capable CPUs/OS.'
    echo 'ARM64 uses the upstream ARMv8 crypto target; ARMv8 AES support required.'
    echo 'OpenCL, CUDA, KawPow and GhostRider disabled for this package.'
    echo 'No global -march=native or AVX512 flag; x86 VAES512 uses a separate translation unit.'
    echo 'hwloc 2.12.1; SHA256 ffa02c3a308275a9339fbe92add054fac8e9a00cb8fe8c53340094012cb7c633'
    cmake --version | head -n 1
    "$compiler" --version | head -n 1
    apk info -v musl gcc g++ libstdc++ libuv libuv-static openssl openssl-libs-static
} > "$dest/BUILD_INFO.txt"
for binary in "$dest/metaxmrig" "$dest/xmrig-baseline"; do
    # A static ELF has neither a dynamic loader nor shared-library dependencies.
    readelf -l "$binary" > "$binary.program-headers.txt"
    readelf -d "$binary" > "$binary.dynamic-section.txt"
    if grep -q INTERP "$binary.program-headers.txt" || grep -q NEEDED "$binary.dynamic-section.txt"; then
        echo "Expected fully static executable: $binary" >&2
        exit 1
    fi
    "$binary" --version
done
tar -czf "$work/$bundle.tar.gz" -C "$work" "$bundle"
(cd "$work" && sha256sum "$bundle.tar.gz" > "$bundle.sha256")
echo "Package: $work/$bundle.tar.gz"
