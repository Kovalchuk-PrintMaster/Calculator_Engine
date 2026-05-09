#!/usr/bin/env python
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    admin_dir = Path(__file__).resolve().parent  # .../app/apps/admin
    repo_root = admin_dir.parents[1]  # .../app

    for path in (str(admin_dir), str(repo_root)):
        if path not in sys.path:
            sys.path.insert(0, path)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "calc_admin.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
