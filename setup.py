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
        'Django>=1.4',
        'django-social-auth>=0.7,<0.8',
        'django-markupfield',
        'dropbox>1.4',
        'Markdown',
        'PyYAML',
        'python-dateutil',
    ],
    test_suite='stardate.tests'
)
