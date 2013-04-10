from distutils.core import setup

setup(
    name = 'btframework',
    version = '0.2',
    description = 'BTFramework',
    license = 'License :: OSI Approved :: Apache Software License',
    author = 'Uche Ogbuji',
    author_email = 'uche@zepheira.com',
    url = 'http://zepheira.com/',
    package_dir={'btframework': 'lib'},
    #packages = ['btframework', 'btframework.akara'],
    packages = ['btframework', 'btframework.contrib'],
    scripts = ['cmdline/readmarcxml.py', 'cmdline/augment_lccn.py', 'cmdline/build_model.py', 'cmdline/build_testcase.py'],
    #http://packages.python.org/distribute/setuptools.html#declaring-dependencies
#    install_requires = ['amara >= 2', 'uritemplate >= 0.5.1'],
)
