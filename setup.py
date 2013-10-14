from setuptools import setup

setup(
    name='stardate',
    version='0.1',
    author=u'Benjamin Turner',
    author_email='benturn@gmail.com',
    packages=[
        'example',
        'example.core',
        'example.example',
        'stardate',
        'stardate.backends',
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
