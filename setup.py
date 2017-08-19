#! /usr/bin/env python3

import pip
import sys

from setuptools import setup

# Check pip version
if (9, 0, 1) > tuple([int(x) for x in pip.__version__.split('.')[:3]]):
    pip_message = f'Please install pip >= 9.0.1, you have version {pip.__version__}'
    print(pip_message, file=sys.stderr)
    sys.exit(1)

long_description = """
`mattbot` is a slack bot.

`mattbot` has tons of features, and can hot-load new commands on the fly.

"""

setup(
    name='mattbot',
    description='mattbot - slack bot',
    version='0.0.1',
    license='MIT',
    author='Matthew Purdon',
    author_email='matthew@codenaked.org',
    url='http://slack.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: Linux',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Scientific/Engineering',
    ],
    keywords="slack bot",

    packages=['mattbot'],
    python_requires='>=3.6.2',
    install_requires=[],
    extras_require={
        ':sys.platform == "linux"': ['pyinotify'],
    },
    long_description=long_description,
    entry_points={
        'console_scripts': [
            'mattbot = mattbot.__main__:main'
        ]
    },
)
