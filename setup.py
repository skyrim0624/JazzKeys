"""
py2app build script for JazzKeys
Usage: python3 setup.py py2app
"""
from setuptools import setup
import subprocess
import os
import glob

# Find portaudio dylib from sounddevice package
site_packages = subprocess.check_output(
    ['python3', '-c', 'import site; print(site.getsitepackages()[0])']
).decode().strip()

portaudio_pattern = os.path.join(site_packages, '_sounddevice_data', 'portaudio-binaries', 'libportaudio.dylib')
portaudio_matches = glob.glob(portaudio_pattern)

frameworks = ['/opt/homebrew/lib/libfluidsynth.dylib']
if portaudio_matches:
    frameworks.append(portaudio_matches[0])
    print(f"Found portaudio: {portaudio_matches[0]}")
else:
    # Try homebrew
    if os.path.exists('/opt/homebrew/lib/libportaudio.dylib'):
        frameworks.append('/opt/homebrew/lib/libportaudio.dylib')
        print("Found portaudio via homebrew")
    else:
        print("WARNING: portaudio not found!")

print(f"Frameworks to bundle: {frameworks}")

APP = ['main.py']
DATA_FILES = [('', ['Piano.sf3'])]
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'app_icon.icns',
    'plist': {
        'CFBundleName': 'JazzKeys',
        'CFBundleDisplayName': 'JazzKeys',
        'CFBundleIdentifier': 'com.andreas.jazzkeys',
        'CFBundleShortVersionString': '1.0.0',
        'LSBackgroundOnly': True,
        'NSHighResolutionCapable': True,
    },
    'includes': ['fluidsynth', 'numpy', 'sounddevice', 'ctypes',
                 'threading', 'argparse', 'random', 'time', 'math'],
    'excludes': ['PyInstaller', 'django', 'cffi', 'Cython', 'numba',
                 'setuptools', 'pip', 'wheel', 'pytest', 'sphinx',
                 'tkinter', 'matplotlib', 'pandas', 'PIL', 'cv2',
                 'scipy', 'sklearn', 'torch', 'tensorflow'],
    'frameworks': frameworks,
    'packages': ['_sounddevice_data', 'pynput'],
    'resources': [],
}

setup(
    name='JazzKeys',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
