from distutils.core import setup

from transtrans import VERSION

setup(name='django-transtrans',
    version='.'.join(map(str, VERSION)),
    author='Aleksander Zdyb',
    author_email='azdyb@live.com',
    description='Transparent translations for Django models',
    long_description=open('README.rst').read(),
    license='BSD',
    url='http://github.com/ojo/django-transtrans',
    packages=["transtrans"],
    classifiers=['Development Status :: 2 - Pre-Alpha',
                'Environment :: Web Environment',
                'Intended Audience :: Developers',
                'License :: OSI Approved :: BSD License',
                'Operating System :: OS Independent',
                'Programming Language :: Python',
                'Topic :: Utilities'],
)
