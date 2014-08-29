django-auth-ldap-ad
===================


## Why
Django authentication backend for LDAP with Active Directory

I created this project since i could not find proper way of doing binding with SASL using  [django-auth-ldap](https://pythonhosted.org/django-auth-ldap/).

Problem is that not all AD setups support TLS. So if SASL is not used the password and username when doing the bind is sent cleartext over the network. SASL provides some security with for example DIGEST-MD5.

While adding support for django-auth-ldap would have been one option, the library looked too heavy for my usecase, and googling gave me messy looking snippet from [snippets](https://djangosnippets.org/snippets/501/) i decided to make minimal AD-backend of my own.


## Installation
Copy the package to your django project root and add it to INSTALLED apps

Required packages: ldap and mockldap for testing

## Usage

      Modify your settings to contain authentication backend, for example
      AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend', 'djangoauth-ldap-ad.backend.LDAPBackend')
      

      AUTH_LDAP_SERVER_URI    = "ldap://localhost:389,ldap://remote_host.org:389"
      AUTH_LDAP_SEARCH_DN     = "DC=mydomain,DC=org"
      AUTH_LDAP_USER_ATTR_MAP = {
         "first_name": "cn",
         "last_name": "sn",
         "email": "email"
         }

      AUTH_LDAP_USER_FLAGS_BY_GROUP = {
         "is_staff" : "CN=SoftwareDeveloper,DC=mydomain",
         "is_superuser" : "CN=WebAdmin,DC=mydomain",
      }
      
      # All people that are to be staff are also to belong to this group  
      AUTH_LDAP_USER_GROUPS_BY_GROUP = {
         "AdminGroup" : AUTH_LDAP_USER_FLAGS_BY_GROUP["is_staff"],
      }
      
      # Map django user preferences
      AUTH_LDAP_USER_ATTR_MAP = {
         "first_name": "givenName",
         "last_name": "sn",
         "email": "mail"
      }


## References

#### CONNECTION_OPTIONS
     Default : { ldap.OPT_REFERRALS : 0} 
  
Set Ldap connection optios, as in [python-ldap options](http://www.python-ldap.org/doc/html/ldap.html#options).
For the default option, see [python ldap faq question 12](http://www.python-ldap.org/faq.shtml).


#### SERVER_URI
     Defaut : 'ldap://localhost',
Comma separated list of servers to be used. Looped until one response is received (negative or positive).

#### USER_FLAGS_BY_GROUP
     Defaut : { }
Dictonary of 'flag_name' : 'required groups'. Set user flags (True/False) if all required groups are found in single memberOf field entry.

#### USER_GROUPS_BY_GROUP
     Defaut : { }
Dictonary of 'group name' : 'required groups'. Adds user to the group  if all required groups are found in single memberOf field entry.



#### USER_ATTR_MAP
     Defaut : { }
Dictonary of 'django user attribute' : 'ldap user attribute' . Maps given ldap attributes to django user attributes.


#### TRACE_LEVEL
     Defaut : 0
Set python LDAP trace level, see [python-ldap](http://www.python-ldap.org/doc/html/ldap.html)

#### SASL_MECH
     Defaut : "DIGEST-MD5"
Set SASL mechanism, see python-ldap manual.


#### SEARCH_DN
     Defaut : "DC=localdomain,DC=ORG"
When performing the user search what to use as startpoint, corresponds to '-b' options in [ldapsearch](http://linux.die.net/man/1/ldapsearch)
     
#### SEARCH_FILTER   
      Default : 'SEARCH_FILTER' : "(SAMAccountName=%(user)s)"
With what to filter the search results.

# Tested with

Django 1.4 and Debian 7








