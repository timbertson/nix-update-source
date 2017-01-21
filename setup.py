from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

def read(relpath):
	with open(path.join(here, *relpath.split('/')), encoding='utf-8') as f:
		return f.read()

setup(
	name='nix-update-source',
	version=read('VERSION'),
	url='https://github.com/timbertson/nix-update-source',
	install_requires=[],
	scripts=['bin/nix-update-source' ]
)

