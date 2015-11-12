from setuptools import find_packages, setup

setup(
    name='django-stardate',
    version='0.1.0.a4',
    author=u'Benjamin Turner',
    author_email='benturn@gmail.com',
    packages=find_packages(),
    url='https://github.com/blturner/django-stardate',
    download_url='https://github.com/blturner/django-stardate/archive/v0.1.0.a4.tar.gz',
    license='BSD',
    description='Another django blog app.',
    zip_safe=False,
    install_requires=[
        'Django>=1.4,<1.9',
        'django-markupfield==1.3.5',
        'dropbox>=1.4,<2.0',
        'Markdown==2.0.3',
        'PyYAML==3.11',
        'python-dateutil==2.1',
        'python-social-auth>=0.1,<0.3',
        'pytz<2014.4',
    ],
)
