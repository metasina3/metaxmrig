#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check startup, hostname lookup and TLS login against an idle local fixture."""
import hashlib
import json
from pathlib import Path
import signal
import socket
import ssl
import subprocess
import sys
import tempfile

binary = Path(sys.argv[1]).resolve()
version = subprocess.check_output([str(binary), '--version'], text=True, timeout=10)
assert 'MetaXMRig' in version and 'OpenSSL/' in version and 'hwloc/' in version, version
help_text = subprocess.check_output([str(binary), '--help'], text=True, timeout=10)
assert '--randomx-aes' in help_text
print(version, end='')

with tempfile.TemporaryDirectory(prefix='meta-tls-test-') as tmp, socket.socket() as server:
    tmp = Path(tmp)
    cert, key = tmp / 'cert.pem', tmp / 'key.pem'
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                    '-keyout', str(key), '-out', str(cert), '-days', '1',
                    '-subj', '/CN=localhost'], check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=15)
    fingerprint = hashlib.sha256(ssl.PEM_cert_to_DER_cert(cert.read_text())).hexdigest()
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(cert, key)
    seen_sni = []
    ctx.set_servername_callback(lambda connection, name, context: seen_sni.append(name))
    server.bind(('127.0.0.1', 0))
    server.listen(1)
    server.settimeout(20)
    port = server.getsockname()[1]
    config = {'autosave': False, 'watch': False, 'colors': False, 'title': False,
              'cpu': {'enabled': False}, 'opencl': {'enabled': False},
              'cuda': {'enabled': False}, 'pools': [
                  {'url': f'localhost:{port}', 'user': 'portability-test',
                   'tls': True, 'sni': True, 'tls-fingerprint': fingerprint, 'coin': 'monero'}]}
    config_path = tmp / 'config.json'
    config_path.write_text(json.dumps(config))
    with (tmp / 'stdout.log').open('w') as log:
        proc = subprocess.Popen([str(binary), '-c', str(config_path),
                                 '--log-file=' + str(tmp / 'miner.log')],
                                cwd=tmp, stdout=log, stderr=subprocess.STDOUT)
        try:
            connection, _ = server.accept()
            connection.settimeout(15)
            with connection, ctx.wrap_socket(connection, server_side=True) as tls:
                data = b''
                while b'\n' not in data:
                    chunk = tls.recv(4096)
                    assert chunk, 'TLS connection closed before login'
                    data += chunk
                    assert len(data) < 65536, 'Oversized login'
                login = json.loads(data.split(b'\n', 1)[0])
                assert login['method'] == 'login', login
                assert login['params']['login'] == 'portability-test', login
                assert seen_sni == ['localhost'], seen_sni
                print(f'OK: localhost lookup, {tls.version()}, pinned certificate, Stratum login; no job sent')
        except Exception:
            print((tmp / 'miner.log').read_text() if (tmp / 'miner.log').exists() else 'No miner log')
            print((tmp / 'stdout.log').read_text())
            raise
        finally:
            if proc.poll() is None:
                proc.send_signal(signal.SIGINT)
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
