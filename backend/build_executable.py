# backend/build_executable.py
import PyInstaller.__main__
import sys
import os

def build_backend():
    # Determine the appropriate executable name based on platform
    if sys.platform.startswith('win'):
        executable_name = 'backend.exe'
    else:
        executable_name = 'backend'

    PyInstaller.__main__.run([
        'app/main.py',  # Your main Python file
        '--name=%s' % executable_name,
        '--onefile',
        '--hidden-import=uvicorn.logging',
        '--hidden-import=uvicorn.loops',
        '--hidden-import=uvicorn.loops.auto',
        '--hidden-import=uvicorn.protocols',
        '--hidden-import=uvicorn.protocols.http',
        '--hidden-import=uvicorn.protocols.http.auto',
        '--hidden-import=uvicorn.lifespan',
        '--hidden-import=uvicorn.lifespan.on',
        '--add-data=app/templates:templates',  # If you have templates
        '--add-data=app/static:static',  # If you have static files
        '--clean',
        '--noconsole'  # Remove this if you want to see console output
    ])

if __name__ == '__main__':
    build_backend()