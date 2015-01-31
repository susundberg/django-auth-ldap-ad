
import ldap,ldap.sasl
from django.contrib.auth.models import User, Group

import six


class LDAPBackendException( Exception ):
   pass

"""
 Main class for handling the authentication
"""
class LDAPBackend(object):
   
    def authenticate(self, username=None, password=None):
        if hasattr( self, "ldap_settings") == False:
           self.ldap_settings = LDAPSettings()
        
        # For all configured servers try to connect
        for server in self.ldap_settings.SERVER_URI:
           
           # Use self.ldap_connection object if such is given for testing with mockldap.
           if hasattr( self, "ldap_connection" ) == False:
              try:
                 ldap_connection = self.ldap_open_connection(server, username, password)
              except ldap.SERVER_DOWN:
                  continue
              except ldap.INVALID_CREDENTIALS:
                  return None
           else:
              ldap_connection = self.ldap_connection
              
           for key,value in self.ldap_settings.CONNECTION_OPTIONS.items():
              ldap_connection.set_option( key , value )

           # Do search
           try:
              ldap_user_info = self.ldap_search_user( ldap_connection,username,password ) 
           except LDAPBackendException:
              return None
           
           return self.get_local_user( username, ldap_user_info )
        return None
        
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
         

    def ldap_open_connection( self, ldap_url, username, password ):
         ldap_session = ldap.initialize(ldap_url,trace_level=self.ldap_settings.TRACE_LEVEL)
         
         sasl_auth = ldap.sasl.sasl( {
               ldap.sasl.CB_AUTHNAME:username,
               ldap.sasl.CB_PASS    :password,
               },
               self.ldap_settings.SASL_MECH
            )
         
         ldap_session.sasl_interactive_bind_s("", sasl_auth)
         return ldap_session
    
    # Search for user, returns users info (dict)
    def ldap_search_user(self, connection, username, password ):


      result_set = []
      ldap_result_id = connection.search( self.ldap_settings.SEARCH_DN , ldap.SCOPE_SUBTREE, self.ldap_settings.SEARCH_FILTER % { "user" : username }) 
      result_all_type, result_all_data = connection.result(ldap_result_id, 1)
      result_entries = []
      for result_type, result_data in result_all_data:
         if result_type != None:
            result_entries.append( result_data )
            
      if len( result_entries ) == 0:
         raise LDAPBackendException("No entries found!")
      
      if len( result_entries ) != 1:
         raise LDAPBackendException("More than one found!")

      return result_entries[0]

    def get_local_user(self, ldap_username, info ):
       username = ldap_username.lower()
       try:
          user = User.objects.get( username = username )
       except User.DoesNotExist:
          # Make new one
          user = User( username = username )
          user.set_unusable_password()
       # refresh memberships
       members_of = []
       for group in info['memberOf']:
          members_of.append( group.lower().split(",") )
       
       # Set first_name or last_name or email ..
       for key, value in self.ldap_settings.USER_ATTR_MAP.items():
          if value in info:
             setattr( user, key, info[value][0] )

       

       def check_for_membership( members_of, required_groups_options ):
         """ Check for membership in given groups,
             Parameter:
                required_groups_options - can be string or list of strings. Each entry must 
                                       be comma-separeted groupnames """
                                       
         if isinstance(required_groups_options, six.string_types):
           required_groups_options = [required_groups_options]
          
         for required_groups in required_groups_options:
            required_groups = required_groups.lower().split(",")
            # check for all members of groups
            for member_of_group in members_of:
               # check that all required groups are in this membership
               requirement_fullfilled = all( (required_group in member_of_group) for required_group in required_groups )
               if requirement_fullfilled:
                  return True
         return False

       # set is_superuser etc
       for wanted_property, requirements in self.ldap_settings.USER_FLAGS_BY_GROUP.items():
         has_property = check_for_membership( members_of, requirements )
         setattr( user, wanted_property, has_property )
       
       # We need to do save before we can use the groups (for m2m binding)
       user.save()
       # user.groups.add( Group.objects.get(name = "ODAdmin"))
       for wanted_group, requirements in self.ldap_settings.USER_GROUPS_BY_GROUP.items():
          if check_for_membership( members_of, requirements ):
              user.groups.add( Group.objects.get(name=wanted_group) )
          else:
              user.groups.remove( Group.objects.get(name=wanted_group) )
       user.save()
       return user
       

         
""" Load settings from Django settigns """
class LDAPSettings(object):
    defaults = {
        'CONNECTION_OPTIONS': { ldap.OPT_REFERRALS : 0},
        'SERVER_URI': 'ldap://localhost',
        'USER_FLAGS_BY_GROUP' : {},
        'USER_GROUPS_BY_GROUP' : {},
        'USER_ATTR_MAP' : {},
        'TRACE_LEVEL' : 0,
        'SASL_MECH' : 'DIGEST-MD5',
        'SEARCH_DN'     : "DC=localdomain,DC=ORG",
        'SEARCH_FILTER' : "(SAMAccountName=%(user)s)"
    }

    def __init__(self, prefix='AUTH_LDAP_'):
        from django.conf import settings

        for name, default in self.defaults.items():
            value = getattr(settings, prefix + name, default)
            setattr(self, name, value)

