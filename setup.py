from setuptools import find_packages, setup

setup(
    name="django-stardate",
    version="0.1.0.a5",
    author=u"Benjamin Turner",
    author_email="benturn@gmail.com",
    packages=find_packages(),
    url="https://github.com/blturner/django-stardate",
    download_url="https://github.com/blturner/django-stardate/archive/v0.1.0.a5.tar.gz",
    license="BSD",
    description="Another django blog app.",
    zip_safe=False,
    install_requires=[
        "Django>=1.4,<1.12",
        "django-markupfield==2.0.1",
        "dropbox==9.5.0",
        "PyYaml==5.1",
        "python-dateutil==2.8.0",
        "pytz<2015.7",
        "social-auth-app-django==2.1.0",
        "watchdog==0.8.3",
    ],
    test_requires=["mock==1.3.0"],
)
