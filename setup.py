from setuptools import setup, find_packages

version = '0.1.0'

setup(
    name='django-microblogging',
    version=version,
    description="django-microblogging",
    classifiers=[
        "Framework :: Django",
        "Programming Language :: Python",
        "Environment :: Web Environment",
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
    ],
    keywords='microblogging,django',
    author='James Tauber',
    author_email='jtauber@jtauber.com',
    maintainer='Jay Graves',
    maintainer_email='jay@skabber.com',
    url='http://code.google.com/p/django-microblogging/',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)