from setuptools import setup, find_packages
from swiftscout import __version__ as version

install_requires = []
try:
    import eventlet
except ImportError:
    install_requires.append("eventlet")
try:
    import json
except ImportError:
    install_requires.append("simplejson")

name = "SwiftScout"

setup(
    name = name,
    version = version,
    author = "Florian Hines",
    author_email = "syn@ronin.io",
    description = "SwiftScout",
    packages=['swiftscout'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6',
        ],
    install_requires=install_requires,
    scripts=['bin/ringscout']
    )

