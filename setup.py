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
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='gliding ogn',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        'Flask==1.1.1',
        'Flask-SQLAlchemy==2.4.1',
        'Flask-Migrate==2.5.3',
        'Flask-Bootstrap==3.3.7.1',
        'Flask-WTF==0.14.3',
        'Flask-Caching==1.8.0',
        'geopy==1.21.0',
        'celery==4.4.1',
        'redis==3.5.0',
        'aerofiles==1.0.0',
        'geoalchemy2==0.7.0',
        'shapely==1.7.0',
        'ogn-client==0.9.6',
        'psycopg2-binary==2.8.4',
        'mgrs==1.3.6',
        'xmlunittest==0.5.0',
        'flower==0.9.3',
        'tqdm==4.45.0',
	'requests==2.23.0',
    ],
    test_require=[
        'pytest==5.0.1',
        'flake8==1.1.1',
        'xmlunittest==0.4.0',
    ],
    zip_safe=False
)
