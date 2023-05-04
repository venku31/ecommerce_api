from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in ecommerce_api/__init__.py
from ecommerce_api import __version__ as version

setup(
	name="ecommerce_api",
	version=version,
	description="Ecommerce Api",
	author="venkatesh",
	author_email="vn2019453@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
