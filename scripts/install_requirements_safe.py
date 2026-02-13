#!/usr/bin/env python3
"""
Install requirements one-by-one and log failures. Cross-platform friendly.
Usage: python scripts/install_requirements_safe.py [requirements-file]
"""
import subprocess
import sys
import os

req_file = sys.argv[1] if len(sys.argv) > 1 else 'requirements.txt'
log_file = 'install_errors.log'

open(log_file, 'w').close()
print(f'Installing packages from {req_file} (one-by-one). Errors will be logged to {log_file}')

with open(req_file) as f:
    for raw in f:
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue

        print(f'Installing: {line}')
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', line])
        if res.returncode != 0:
            with open(log_file, 'a') as L:
                L.write(f'{line}\n')

print('Done. Check install_errors.log for any failed packages.')
if os.path.getsize(log_file) > 0:
    sys.exit(1)
