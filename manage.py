#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Auto-fix Anaconda SQLite DLL loading on Windows
if sys.platform == 'win32':
    for dll_dir in [
        r'C:\ProgramData\Anaconda3\Library\bin',
        r'C:\ProgramData\Anaconda3\DLLs',
        r'C:\ProgramData\Anaconda3',
    ]:
        if os.path.exists(dll_dir):
            try:
                os.add_dll_directory(dll_dir)
            except Exception:
                pass
            os.environ['PATH'] = dll_dir + os.pathsep + os.environ.get('PATH', '')


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
