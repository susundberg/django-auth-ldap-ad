from setuptools import setup

url = "https://github.com/susundberg/django-auth-ldap-ad"
long_description = url

setup(
    name = "django-auth-ldap-ad",
    author = "Pauli",
    author_email = "susundberg@gmail.com",
    description = "Django authentication backend for LDAP with Active Directory",
    license = "GPLv2",
    url = url,
    version = "2.0.0",
    packages = ["django_auth_ldap_ad"],
    long_description = long_description,
    install_requires = ["python-ldap", "Django>=1.4,<=1.9"]
)
