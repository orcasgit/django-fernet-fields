from os.path import join
from setuptools import setup, find_packages


long_description = (
    open('README.rst').read() + open('CHANGES.rst').read())


def get_version():
    with open(join('fernet_fields', '__init__.py')) as f:
        for line in f:
            if line.startswith('__version__ ='):
                return line.split('=')[1].strip().strip('"\'')


setup(
    name='singular-django-fernet-fields',
    version=get_version(),
    description="Fernet-encrypted model fields for Django",
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author='ORCAS, Inc',
    author_email='orcastech@orcasinc.com',
    url='https://github.com/orcasgit/django-fernet-fields/',
    packages=find_packages(),
    install_requires=['Django>=1.11', 'cryptography>=0.9'],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Framework :: Django',
    ],
    zip_safe=False,
)
