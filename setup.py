from distutils.core import setup

setup(
    name = 'btframework',
    version = '0.1',
    description = 'BTFramework',
    license = 'License :: OSI Approved :: Apache Software License',
    author = 'Uche Ogbuji',
    author_email = 'uche@zepheira.com',
    url = 'http://zepheira.com/',
    package_dir={'btframework': 'lib'},
    #packages = ['btframework', 'btframework.akara'],
    packages = ['btframework', 'btframework.contrib'],
)
