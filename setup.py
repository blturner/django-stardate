from setuptools import find_packages, setup

setup(
    name='django-stardate',
    version='0.1.0.a5',
    author=u'Benjamin Turner',
    author_email='benturn@gmail.com',
    packages=find_packages(),
    url='https://github.com/blturner/django-stardate',
    download_url='https://github.com/blturner/django-stardate/archive/v0.1.0.a5.tar.gz',
    license='BSD',
    description='Another django blog app.',
    zip_safe=False,
    install_requires=[
        'Django>=1.4,<1.10',
        'django-markupfield==1.4.0',
        'dropbox>=1.4,<4.0',
        'Markdown==2.6.5',
        'PyYAML==3.11',
        'python-dateutil==2.4.2',
        'python-social-auth>=0.1,<0.3',
        'pytz<2015.7',
    ],
    test_requires=['mock==1.3.0',]
)
