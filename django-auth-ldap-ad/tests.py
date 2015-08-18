


import mockldap
import ldap

import django_ldap_ad.backend as backend

from django.test import TestCase
from django.utils import unittest

from django.contrib.auth.models import User, Group


class TestSettings(backend.LDAPSettings):
    def __init__(self, **kwargs):
        for name, default in self.defaults.items():
            value = kwargs.get(name, default)
            setattr(self, name, value)

class LDAPBackendTest(TestCase):
    top = ('o=test', {'o': 'test'})
    alice = ('cn=alice,ou=example,o=test', {'SAMAccountName': ['alice'], 'userPassword': ['alicepw'], 'memberOf' : ["dc=test,cn=admin,cn=extra,cn=fake,ou=foo",
                                                                                                                    "dc=test,cn=superuser,cn=extra,cn=fake,ou=foo",
                                                                                                                    "dc=test,cn=fakuser,cn=extra,cn=fake,ou=foo"]  })

    # This is the content of our mock LDAP directory. It takes the form
    # {dn: {attr: [value, ...], ...}, ...}.
    directory = dict([top, alice])

    @classmethod
    def setUpClass(cls):
        # We only need to create the MockLdap instance once. The content we
        # pass in will be used for all LDAP connections.
        cls.mockldap = mockldap.MockLdap(cls.directory)

    @classmethod
    def tearDownClass(cls):
        del cls.mockldap

    def setUp(self):
        self.mockldap.start()
        self.ldapobj = self.mockldap['ldap://localhost/']
        self.backend = backend.LDAPBackend()
        self.backend.ldap_connection = self.ldapobj 

    def tearDown(self):
        # Stop patching ldap.initialize and reset state.
        self.mockldap.stop()
        del self.ldapobj
        

    def tearDown(self):
        self.mockldap.stop()
        del self.ldapobj
    
    def _init_settings(self, **kwargs):
        self.backend.ldap_settings = TestSettings(**kwargs)
    
    def test_options(self):
        self._init_settings(
            SEARCH_DN = "o=test",
            CONNECTION_OPTIONS = {'opt1': 'value1'}
        )
        self.backend.authenticate(username='alice', password='alicepw')
        self.assertEqual(self.ldapobj.get_option('opt1'), 'value1')

    def test_server_uri_string(self):
        self._init_settings(
            SEARCH_DN = "o=test",
            SERVER_URI = "ldap://localhost/"
        )
        self.backend.authenticate(username='alice', password='alicepw')
      
    def test_server_uri_list(self):
        self._init_settings(
            SEARCH_DN = "o=test",
            SERVER_URI = ["ldap://127.0.0.1", "ldap://localhost/" ]
        )
        self.backend.authenticate(username='alice', password='alicepw')
        
        
    def test_bad_person(self):
        self._init_settings(
            SEARCH_DN = "o=test",
        )
        self.assertEqual( User.objects.filter( username="veikko" ).count(), 0 )
        self.backend.authenticate(username='veikko', password='alicepw')
        self.assertEqual( User.objects.filter( username="veikko" ).count(), 0 )
        
    # Well this would be nice, but since we dont have bind its not going to hapen    
    # def test_bad_password(self):

    def test_user_creation(self):
        self._init_settings(
            SEARCH_DN = "o=test",
        )
        self.assertEqual( User.objects.filter( username="alice" ).count(), 0 )
        self.backend.authenticate(username='alice', password='alicepw')
        self.assertEqual( User.objects.filter( username="alice" ).count(), 1 )
        self.backend.authenticate(username='alice', password='alicepw')
        self.assertEqual( User.objects.filter( username="alice" ).count(), 1 )
        
    def test_user_properties(self):     
        self._init_settings(
            SEARCH_DN = "o=test",
            USER_ATTR_MAP = {'first_name' : 'userPassword' }
        )
        self.backend.authenticate(username='alice', password='alicepw')
        user_alice = User.objects.get( username="alice" )
        self.assertEqual( user_alice.first_name, 'alicepw' )
        
    def test_user_flags_000(self):     
        self._init_settings(
            SEARCH_DN = "o=test",
            USER_FLAGS_BY_GROUP = {'is_superuser' : 'cn=superuser', 
                                   'is_staff' : 'cn=is_staff_not_found' }
            )
        
        self.backend.authenticate(username='alice', password='alicepw')
        user_alice = User.objects.get( username="alice" )
        self.assertEqual( user_alice.is_superuser , True )
        self.assertEqual( user_alice.is_staff , False )
    
    def test_user_flags_001(self):     
        self._init_settings(
            SEARCH_DN = "o=test",
            USER_FLAGS_BY_GROUP = {'is_superuser' : 'cn=superuser,dc=test_not_found', 
                                   'is_staff' : 'cn=fake,cn=superuser,ou=foo' }
            )
        
        self.backend.authenticate(username='alice', password='alicepw')
        user_alice = User.objects.get( username="alice" )
        self.assertEqual( user_alice.is_superuser , False )
        self.assertEqual( user_alice.is_staff , True )
        
    def test_user_flags_002(self):   
        self._init_settings(
            SEARCH_DN = "o=test",
            USER_FLAGS_BY_GROUP = {'is_superuser' : ['cn=superuser,dc=test_not_found','cn=fake,cn=superuser,ou=foo'] 
                                   }
            )
        
        self.backend.authenticate(username='alice', password='alicepw')
        user_alice = User.objects.get( username="alice" )
        self.assertEqual( user_alice.is_superuser , True )
        
    def test_user_groups(self):
       group_admin = Group.objects.create(name = "MyAdmins")
       group_pony = Group.objects.create(name = "MyPonies")
       
       self._init_settings(
            SEARCH_DN = "o=test",
            USER_GROUPS_BY_GROUP = {'MyAdmins' : 'cn=superuser,dc=test_not_found', 
                                    'MyPonies' : 'cn=fake,cn=superuser,ou=foo' }
            )

       self.backend.authenticate(username='alice', password='alicepw')
       user_alice = User.objects.get( username="alice" )
       self.assertEqual( user_alice.groups.filter(name="MyAdmins").count(), 0)
       self.assertEqual( user_alice.groups.filter(name="MyPonies").count(), 1)
       
       # Check also removal
       user_alice.groups.add( group_admin )
       user_alice.save()
       
       self.assertEqual( user_alice.groups.filter(name="MyAdmins").count(), 1)
       
       self.backend.authenticate(username='alice', password='alicepw')
       user_alice = User.objects.get( username="alice" )
       self.assertEqual( user_alice.groups.filter(name="MyAdmins").count(), 0)
       self.assertEqual( user_alice.groups.filter(name="MyPonies").count(), 1)
       
    def test_user_groups_001(self):
       """ Test for groups list requirements """
       group_pony = Group.objects.create(name = "MyPonies")
       self._init_settings(
            SEARCH_DN = "o=test",
            USER_GROUPS_BY_GROUP = { 'MyPonies' : ('cn=superuser,dc=test_not_found', 'cn=fake,cn=superuser,ou=foo') }
            )
       self.backend.authenticate(username='alice', password='alicepw')
       user_alice = User.objects.get( username="alice" )
       self.assertEqual( user_alice.groups.filter(name="MyPonies").count(), 1)
       
       
       
