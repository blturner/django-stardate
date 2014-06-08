from setuptools import setup

setup(
    name='django-stardate',
    version='0.1.0.a1',
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
        'Django>=1.4,<1.7',
        'django-markupfield',
        'dropbox>1.4,<2.1.0',
        'Markdown',
        'PyYAML',
        'python-dateutil',
        'python-social-auth>=0.1',
    ],
    test_suite='stardate.tests'
)
