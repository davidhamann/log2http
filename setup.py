from setuptools import setup

with open("README.md", "r") as ld:
    long_description = ld.read()

setup(
    name='log2http',
    version='0.1.1',
    python_requires='>=3.6',
    author='David Hamann',
    author_email='dh@davidhamann.de',
    description='log2http watches log files and sends new contents to a specified http endpoint.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/davidhamann/log2http',
    packages=['log2http'],
    include_package_data=True,
    install_requires=[
        'requests>=2',
        'docopt>=0.6.2',
        'mypy_extensions>=0.4.1',
        'PyYAML>=3.13'
    ],
    entry_points={
        'console_scripts': ['log2http=log2http.app:main']
    },
    classifiers=(
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: System Administrators',
        'Operating System :: Unix',
        'Environment :: Console'
    )
)
