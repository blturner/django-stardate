import os

from setuptools import setup

version_file = open(os.path.join(__file__, 'VERSION'))
version = version_file.read().strip()

setup(
    version=version,
    name='django-stardate',
    author=u'Benjamin Turner',
    author_email='benturn@gmail.com',
    packages=[
        'stardate',
        'stardate.backends',
        'stardate.management.commands',
        'stardate.tests',
        'stardate.urls',
    ],
    url='https://github.com/blturner/django-stardate',
    license='BSD',
    description='Another django blog app.',
    # long_description=open('README').read(),
    zip_safe=False,
    install_requires=[
        'Django',
        'django-social-auth',
        'django-markupfield',
        'dropbox',
        'Markdown',
        'PyYAML',
        'python-dateutil',
    ],
    test_suite='stardate.tests'
)
