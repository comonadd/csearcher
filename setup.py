from setuptools import setup, find_packages
from distutils.core import Extension

cpp_handler_module = Extension(
        'cpp_handler',
        sources=["codesearch/handlers/cpp_handler.cpp"],
        libraries=['clang'],
)


with open('requirements.txt') as f:
    requirements = f.readlines()

with open('README.md') as f:
    long_description = f.read()

setup(
        name ='codesearcher',
        version ='1.0.0',
        author ='Dmitry Guzeev',
        author_email ='dmitri.guzeev@gmail.com',
        url ='https://github.com/comonadd/codesearcher',
        description ='Demo Package for GfG Article.',
        long_description = long_description,
        long_description_content_type = "text/markdown",
        license ='MIT',
        packages = find_packages(),
        entry_points ={
            'console_scripts': [
                'csr = codesearch.cli:main'
            ]
        },
        classifiers = [
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
        keywords ='code search',
        install_requires = requirements,
        zip_safe = False,
        ext_modules=[cpp_handler_module],
)
