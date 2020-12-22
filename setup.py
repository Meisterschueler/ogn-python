#!/usr/bin/env python3

from os import path
from setuptools import setup, find_packages


here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ogn-python',
    version='0.5.0',
    description='A database backend for the Open Glider Network',
    long_description=long_description,
    url='https://github.com/glidernet/ogn-python',
    author='Konstantin Gründger aka Meisterschueler, Fabian P. Schmidt aka kerel, Dominic Spreitz',
    author_email='kerel-fs@gmx.de',
    license='AGPLv3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: GIS',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9-dev'
    ],
    keywords='gliding ogn',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        'Flask==1.1.2',
        'Flask-SQLAlchemy==2.4.4',
        'Flask-Migrate==2.5.3',
        'Flask-Bootstrap==3.3.7.1',
        'Flask-WTF==0.14.3',
        'Flask-Caching==1.9.0',
        'Flask-Profiler==1.8.1',
        'geopy==2.0.0',
        'celery==4.4.7',
        'Flask-Redis==0.4.0',
        'redis==3.5.3',
        'aerofiles==1.0.0',
        'geoalchemy2==0.8.4',
        'shapely==1.7.1',
        'ogn-client==1.0.1',
        'mgrs==1.4.0',
        'psycopg2-binary==2.8.6',
        'xmlunittest==0.5.0',
        'flower==0.9.7',
        'tqdm==4.54.1',
        'requests==2.25.1',
        'matplotlib==3.3.3',
        'bokeh==2.2.3',
        'pandas==1.1.5',
        'flydenity==0.1.5'
    ],
    test_require=[
        'pytest==5.0.1',
        'flake8==1.1.1',
        'xmlunittest==0.4.0',
    ],
    zip_safe=False
)
