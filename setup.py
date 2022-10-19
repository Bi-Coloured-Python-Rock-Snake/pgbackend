
from setuptools import setup, find_packages

packages = ['pgbackend'] + find_packages('pgbackend')

setup(name="pgbackend",
      version="0.1.0",
      author="Vitalii Abetkin",
      author_email="abvit89s@gmail.ru",
      packages=packages,
      install_requires=['psycopg[pool]'],
      description="pgbackend",
      long_description="pgbackend",
      license="MIT",
      classifiers=())
