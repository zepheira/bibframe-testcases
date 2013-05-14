from distutils.core import setup

setup(
    name = 'bibframe-testcases',
    version = '0.3',
    description = 'BIBFRAME Test Cases',
    license = 'License :: OSI Approved :: Apache Software License',
    author = 'Uche Ogbuji',
    author_email = 'uche@zepheira.com',
    url = 'http://zepheira.com/',
    #Botstrap until we have a main BTF package
    package_dir={'bibframe.testcases': 'lib', 'bibframe': 'bootstrap'},
    packages = ['bibframe', 'bibframe.testcases'],
    scripts = ['cmdline/build_testcase.py'],
    package_data={'bibframe.testcases': ['resource/*']},  # http://docs.python.org/2/distutils/setupscript.html#installing-package-data
    #data_files=[('bibframe.testcases/resource', ['resource/test-template.html'])],  # http://docs.python.org/2/distutils/setupscript.html#installing-additional-files
    #http://packages.python.org/distribute/setuptools.html#declaring-dependencies
#    install_requires = ['amara >= 2', 'uritemplate >= 0.5.1'],
)

