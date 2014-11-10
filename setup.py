from setuptools import setup

setup(
    name='django-stardate',
    version='0.1.0.a2',
    author=u'Benjamin Turner',
    author_email='benturn@gmail.com',
    packages=[
        'stardate',
        'stardate.backends',
        'stardate.management',
        'stardate.management.commands',
        'stardate.tests',
        'stardate.urls',
    ],
    package_data={
        'stardate': [
            'templates/stardate/includes/*.html',
            'templates/stardate/*.html',
        ],
    },
    url='https://github.com/blturner/django-stardate',
    download_url='https://github.com/blturner/django-stardate/archive/v0.1.0.a2.tar.gz',
    license='BSD',
    description='Another django blog app.',
    # long_description=open('README').read(),
    zip_safe=False,
    install_requires=[
        'Django>=1.4,<1.7',
        'django-markupfield==1.1.1',
        'dropbox>=1.4,<2.0',
        'Markdown==2.0.3',
        'PyYAML==3.11',
        'python-dateutil==2.1',
        'python-social-auth>=0.1,<0.2',
        'pytz<2014.4',
    ],
    test_suite='stardate.tests'
)
