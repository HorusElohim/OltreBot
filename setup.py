from setuptools import setup, find_packages


with open('requirements.txt') as f:
    requirements = f.read().splitlines()

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

MODULES = ['bot' , 'cogs' , 'data', 'logger', 'manager']

def get_package_name():
    return 'tdbm'

def produce_module_dot(name):
    return f'{get_package_name()}.{name}'

def produce_module_slash(name):
    return f'{get_package_name()}/{name}'

def produce_import_module(name):
    return {produce_module_dot(name):
                produce_module_slash(name)}

def produce_packages_dirs():
    packages_dirs = {get_package_name() : get_package_name()}

    for module in MODULES:
        packages_dirs.update(produce_import_module(module))

    return packages_dirs

def produce_packages():
    packages = [get_package_name()]

    for module in MODULES:
        packages.append(produce_module_dot(module))

    return packages



setup(
    name='tdbm',
    author='MarkNo1',
    url='https://github.com/MarkNo1-github/TournamentDiscordBot',
    version='0.0.4',
    license=license,
    description='Manage Tournament in Discord',
    long_description=readme,
    package_dir=produce_packages_dirs(),
    packages=produce_packages(),
    entry_points ={'console_scripts': ['tdbm = tdbm.manager:main']},
    install_requires=requirements,
    include_package_data=True,
    python_requires='>=3.6'
)
