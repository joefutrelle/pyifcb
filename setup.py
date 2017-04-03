from setuptools import setup, find_packages


def version():
    with open('VERSION') as f:
        return f.read().strip()


def readme():
    with open('README.md', 'rb') as f:
        return f.read().decode('utf-8', errors='ignore')


reqs = [line.strip() for line in open('requirements.txt') if not line.startswith('#')]


setup(
    name                = "pyifcb",
    version             = version(),
    description         = "A python library for reading Imaging FlowCytobot data",
    long_description    = readme(),
    license             = 'MIT',
    author              = "Joe Futrelle",
    author_email        = "jfutrelle@whoi.edu",
    url                 = "https://github.com/joefutrelle/pyifcb",
    packages            = find_packages(),
    install_requires    = reqs,
    classifiers         = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering',
    ],
    include_package_data = True,
)
