from distutils.core import setup

setup(
    name = 'bibframe-testcases',
    version = '0.3',
    description = 'BIBFRAME Test Cases',
    license = 'License :: OSI Approved :: Apache Software License',
    author = 'Uche Ogbuji',
    author_email = 'uche@zepheira.com',
    url = 'http://zepheira.com/',
    #package_dir={'bibframe.testcases': 'lib'},
    #packages = ['bibframe', 'bibframe.contrib'],
    scripts = ['builder/build_testcase.py'],
    #http://packages.python.org/distribute/setuptools.html#declaring-dependencies
#    install_requires = ['amara >= 2', 'uritemplate >= 0.5.1'],
)

