from setuptools import setup, find_namespace_packages

PackageName = "OltreBot"
AUTHOR = "HorusElohim"
VERSION = "0.3"

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name=PackageName,
    author=AUTHOR,
    url='https://github.com/HorusElohim/NetNode',
    version=VERSION,
    license=license,
    description='',
    long_description=readme,
    packages=find_namespace_packages(include=[PackageName, f'{PackageName}.*']),
    entry_points={'console_scripts': [f'{PackageName} = {PackageName}.scripts.run_bot:main']},
    install_requires=requirements,
    include_package_data=True,
    python_requires='>=3.7'
)
