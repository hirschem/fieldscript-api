#!/usr/bin/env python3
"""
Run Alembic migrations using the current DATABASE_URL.
Usage: python scripts/migrate.py
"""
import os
import sys
import subprocess

alembic_ini = os.path.join(os.path.dirname(__file__), '..', 'alembic.ini')

if not os.path.exists(alembic_ini):
    print("alembic.ini not found!", file=sys.stderr)
    sys.exit(1)

cmd = [sys.executable, '-m', 'alembic', '-c', alembic_ini, 'upgrade', 'head']
print(f"Running: {' '.join(cmd)}")
ret = subprocess.call(cmd)
sys.exit(ret)
