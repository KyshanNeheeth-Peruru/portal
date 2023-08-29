import os
import logging
import environ
from pathlib import Path
from apply import helper
from apply.constants import LDAPActionNames, LDAPEmailBody
from ldap3 import ALL, Server, Connection, NTLM, SUBTREE, SAFE_SYNC, MODIFY_REPLACE

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

logger = logging.getLogger(__name__)


class LDAPHelper:
    def __init__(self, **kwargs):
        self.server_uri = env("SERVER_URI")
        self.admin = env("LDAP_ADMIN")
        self.password = env("LDAP_PASSWORD")
        self.userName = kwargs.get("userName")
        # self.fullName = self.get_ldap_users()
        # self.user_dn = self.get_ldap_users_dn()
        self.fullName = self.get_ldap_users()
        self.user_dn = f"cn={self.fullName},ou=People,dc=winpcs,dc=cs,dc=umb,dc=edu"

    def connect_ldap_server(self):
        try:
            # Provide the hostname and port number of the openLDAP
            server = Server(self.server_uri, get_info=ALL, use_ssl=True)

            # username and password can be configured during openldap setup
            connection = Connection(
                server,
                self.admin,
                self.password,
                client_strategy=SAFE_SYNC,
                auto_bind=True,
            )

            # bind_response = connection.bind()  # Returns True or False
            return connection
        except Exception as ex:
            logger.error(ex)

    def unlock_ldap_account(self):
        # Bind connection to LDAP server
        ldap_conn = self.connect_ldap_server()

        try:
            # isAccountUnlocked = ldap_conn.extend.microsoft.unlock_account(self.user_dn)
            # isAccountNormal = ldap_conn.modify(self.user_dn, {"userAccountControl": [("MODIFY_REPLACE", 512)]})
            # if isAccountUnlocked and isAccountNormal:
            #     ldap_conn.unbind()
                
                
            ldap_conn.extend.microsoft.unlock_account(self.user_dn)
            ldap_conn.modify(self.user_dn, {"userAccountControl": [("MODIFY_REPLACE", 512)]})
            ldap_conn.unbind()
            # else:
            #     helper.send_email(self.userName,
            #                       LDAPActionNames.UNLOCK_ACCOUNT,
            #                       LDAPEmailBody.UNLOCK_ACCOUNT)
            #     logger.debug(f"User:{self.userName} account is not unlocked")
        except Exception as ex:
            helper.send_email(self.userName,
                              LDAPActionNames.ERROR_UNLOCK_ACCOUNT,
                              LDAPEmailBody.ERROR_UNLOCK_ACCOUNT, str(ex))
            logger.error(ex)
    
    # def unlock_ldap_account(self):
    #     ldap_conn = self.connect_ldap_server()
    #     try:
    #         isAccountUnlocked = ldap_conn.extend.microsoft.unlock_account(self.user_dn)
    #         if isAccountUnlocked:
    #             modification = {'userAccountControl': [(MODIFY_REPLACE, [512])]}
    #             isAccountNormal = ldap_conn.modify(self.user_dn, modification)
    #             if isAccountNormal:
    #                 ldap_conn.unbind()
    #             else:
    #                 helper.send_email(self.userName,
    #                               LDAPActionNames.UNLOCK_ACCOUNT,
    #                               LDAPEmailBody.UNLOCK_ACCOUNT)
    #             logger.debug(f"User:{self.userName} account is not set to normal state")
    #         else:
    #             helper.send_email(self.userName,
    #                           LDAPActionNames.UNLOCK_ACCOUNT,
    #                           LDAPEmailBody.UNLOCK_ACCOUNT)
    #             logger.debug(f"User:{self.userName} account is not unlocked")

    #     except Exception as ex:
    #         helper.send_email(self.userName,
    #                       LDAPActionNames.ERROR_UNLOCK_ACCOUNT,
    #                       LDAPEmailBody.ERROR_UNLOCK_ACCOUNT, str(ex))
    #         logger.error(ex)

    def add_user_to_courses(self, course):
        # Bind connection to LDAP server
        ldap_conn = self.connect_ldap_server()

        # group_dn = f"cn={course},ou=Groups,dc=cs,dc=local"
        group_dn = f"cn={course},ou=Groups,dc=winpcs,dc=cs,dc=umb,dc=edu"

        try:
            # print("names:")
            # print(self.user_dn)
            # print(group_dn)
            isUserAdded = ldap_conn.extend.microsoft.add_members_to_groups(
                self.user_dn, group_dn
            )
            # isUserAdded=False

            if isUserAdded:
                ldap_conn.unbind()
            else:
                # helper.send_email(self.userName,
                #                   LDAPActionNames.ADD_USER_TO_COURSE,
                #                   LDAPEmailBody.ADD_USER_TO_COURSE)
                # print(self.user_dn)
                logger.debug(f"User:{self.userName} is not added to {course}")
        except Exception as ex:
            # helper.send_email(self.userName,
            #                   LDAPActionNames.ERROR_ADD_USER_TO_COURSE,
            #                   LDAPEmailBody.ERROR_ADD_USER_TO_COURSE, str(ex))
            print(ex)
            logger.error(ex)

    def change_password(self, password):
        # Bind connection to LDAP server
        ldap_conn = self.connect_ldap_server()

        try:
            isPasswordChanged = ldap_conn.extend.microsoft.modify_password(
                self.user_dn, password
            )
            if isPasswordChanged:
                logger.debug(f"User:{self.userName} Password changed")
                helper.send_email(self.userName,
                                  LDAPActionNames.PASSWORD_CHANGED,
                                  LDAPActionNames.PASSWORD_CHANGED)
            else:
                helper.send_email(self.userName,
                                  LDAPActionNames.CHANGE_PASSWORD,
                                  LDAPActionNames.CHANGE_PASSWORD)
                logger.debug(f"User:{self.userName} Password is not Changed")
        except Exception as ex:
            helper.send_email(self.userName,
                              LDAPActionNames.ERROR_CHANGE_PASSWORD,
                              LDAPEmailBody.ERROR_CHANGE_PASSWORD, str(ex))
            logger.error(ex)

    # Change it to retrieve user's firstname
    def get_ldap_users(self):
        # Provide a search base to search for.
        search_base = 'ou=People,dc=winpcs,dc=cs,dc=umb,dc=edu'
        # provide a uidNumber to search for. '*" to fetch all users/groups
        search_filter = "(cn=*)"

        # Establish connection to the server
        ldap_conn = self.connect_ldap_server()
        
        if(ldap_conn):
            print("success connection")
            try:
                results = ldap_conn.search(search_base,
                                       "(&(objectClass=person)(sAMAccountName=" + str(self.userName) + "))",
                                       attributes=['cn'])
                entries_list = results[2]
                entry_dict = entries_list[0]
                cn_value = entry_dict['attributes']['cn']
                
                if results:
                    return cn_value
                else:
                    raise Exception
            except Exception as e:
                print(e)
        else:
            print("connection error")
            
    def get_ldap_users_dn(self):
        search_base = 'ou=People,dc=winpcs,dc=cs,dc=umb,dc=edu'
        ldap_conn = self.connect_ldap_server()

        try:
            results = ldap_conn.search(search_base,"(&(objectClass=person)(sAMAccountName=" + str(self.userName) + "))",attributes=['distinguishedName'])
            if results:
                return ldap_conn.entries[0].distinguishedName[0]
            else:
                raise Exception
        except Exception as e:
            print(e)

    def get_uid_number(self):
        # provide a uidNumber to search for. '*" to fetch all users/groups
        # search_filter = '(&(objectClass=user)(sAMAccountName=*))'
        search_base = 'ou=People,dc=winpcs,dc=cs,dc=umb,dc=edu'

        # Establish connection to the server
        ldap_conn = self.connect_ldap_server()
        try:
            results = ldap_conn.search(search_base,
                                       "(&(objectClass=person)(sAMAccountName=" + str(self.userName) + "))",
                                       attributes=['uidNumber'])
            print("results:")
            entries_list = results[2]
            entry_dict = entries_list[0]
            uid_num = entry_dict['attributes']['uidNumber']
            print(uid_num)
            if results:
                return ldap_conn.entries[0].uidNumber[0]
            else:
                raise Exception
        except Exception as e:
            print(e)