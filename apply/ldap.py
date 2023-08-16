import os
import logging
import environ
from pathlib import Path
from apply import helper
from apply.remote_connect import RemoteConnect
from apply.constants import LDAPActionNames, LDAPEmailBody
from ldap3 import ALL, NTLM, Connection, Server, SUBTREE, SAFE_SYNC


BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

logger = logging.getLogger(__name__)


class LDAP:
    def __init__(self, **kwargs):
        self.server_uri = env("SERVER_URI")
        self.admin = env("LDAP_ADMIN")
        self.password = env("LDAP_PASSWORD")
        self.userName = kwargs.get("userName")
        self.userPassword = kwargs.get("userPassword")
        self.fullName = kwargs.get("fullName")
        self.firstName = kwargs.get("firstName")
        self.lastName = kwargs.get("lastName")
        self.email = kwargs.get("email")
        self.uid = kwargs.get("userName")
        # self.uidNumber = self.get_ldap_users()
        self.uidNumber = self.get_ldap_users3()
        self.user_dn = f"cn={self.fullName},ou=People,dc=winpcs,dc=cs,dc=umb,dc=edu"
        self.OBJECT_CLASS = ["top", "person", "organizationalPerson", "user"]
        self.ldap_attr = {
            "objectClass": self.OBJECT_CLASS,
            "gidNumber": 10241,
            "givenName": self.firstName,
            "displayName": self.fullName,
            "sn": self.lastName,
            "sAMAccountName": self.userName,
            "userPrincipalName": f"{self.userName}@winpcs.cs.umb.edu",
            "userAccountControl": 512,
        }

    def connect_ldap_server(self):
        try:
            # Provide the hostname and port number of the openLDAP
            server = Server(self.server_uri, get_info=ALL)

            # username and password can be configured during openldap setup
            connection = Connection(
                server,
                self.admin,
                self.password,
                client_strategy=SAFE_SYNC,
                auto_bind=True,
            )
            # bind_response = connection.bind()  # Returns True or False
            logger.info(f"LDAP Connection established..")
            return connection
        except Exception as ex:
            logger.error("Error in Connecting to ldap server", ex)

    def add_new_user(self):
        # Bind connection to LDAP server
        ldap_conn = self.connect_ldap_server()

        try:
            isUserAdded = ldap_conn.add(self.user_dn, attributes=self.ldap_attr)
            if isUserAdded:
                #ldap_conn.extend.microsoft.unlock_account(self.user_dn)  #unlocking here
                #ldap_conn.modify(self.user_dn, {"userAccountControl": [("MODIFY_REPLACE", 512)]})    #unlocking here
                ldap_conn.unbind()
                self.set_new_user_password()
                logger.info(f"User:{self.userName}  is added to LDAP")
            else:
                helper.send_email(self.userName,
                                  LDAPActionNames.USER_EXISTS,
                                  LDAPEmailBody.USER_EXISTS)
                logger.debug(f"User:{self.userName}  is not added")
            
            
            
            # self.connect_ldap_server().add(self.user_dn, attributes=self.ldap_attr)
            # ldap_conn.unbind()
            # self.set_new_user_password()
            # logger.info(f"User:{self.userName}  is added to LDAP")

        except Exception as ex:
            # helper.send_email(self.userName,
            #                   LDAPActionNames.ADD_NEW_USER,
            #                   LDAPActionNames.ADD_NEW_USER, str(ex))

            logger.error(f"Error on Adding new User to LDAP. user_name: {self.userName}", ex)

    def set_new_user_password(self):
        # Bind connection to LDAP server
        ldap_conn = self.connect_ldap_server()

        try:
            isPasswordSet = ldap_conn.extend.microsoft.modify_password(
                self.user_dn, self.userPassword
            )
            if isPasswordSet:
                ldap_conn.unbind()
                self.set_user_attributes()
            else:
                helper.send_email(self.userName,
                                  LDAPActionNames.SET_NEW_USER_PASSWORD,
                                  LDAPEmailBody.SET_NEW_USER_PASSWORD)
                logger.debug(f"User:{self.userName} password is not set")
        except Exception as ex:
            helper.send_email(self.userName,
                              LDAPActionNames.ERROR_NEW_USER_PASSWORD,
                              LDAPEmailBody.ERROR_NEW_USER_PASSWORD, str(ex))
            logger.error(f"Error in Adding Password to new User. user_name: {self.userName}", ex)

    def set_user_attributes(self):
        # Bind connection to LDAP server
        ldap_conn = self.connect_ldap_server()

        try:
            isAccountNormal = ldap_conn.modify(
                self.user_dn,
                {
                    "uid": [("MODIFY_REPLACE", self.uid)],
                    "uidNumber": [("MODIFY_REPLACE", self.uidNumber)],
                    "mail": [("MODIFY_REPLACE", self.email)],
                },
            )
            if isAccountNormal:
                ldap_conn.unbind()
                self.add_user_to_ugrad()
            else:
                helper.send_email(self.userName,
                                  LDAPActionNames.SET_NEW_USER_ATTRIBUTES,
                                  LDAPEmailBody.SET_NEW_USER_ATTRIBUTES)
                logger.debug(f"User:{self.userName} attributes is not set")
        except Exception as ex:
            helper.send_email(self.userName,
                              LDAPActionNames.ERROR_NEW_USER_ATTRIBUTES,
                              LDAPEmailBody.ERROR_NEW_USER_ATTRIBUTES, str(ex))
            logger.error(f"Error in setting attributes to new User. user_name: {self.userName}", ex)

    def add_user_to_ugrad(self):
        # Bind connection to LDAP server
        ldap_conn = self.connect_ldap_server()
        group_dn = "cn=ugrad,ou=Groups,dc=winpcs,dc=cs,dc=umb,dc=edu"

        try:
            isUserAdded = ldap_conn.extend.microsoft.add_members_to_groups(
                self.user_dn, group_dn
            )
            if isUserAdded:
                ldap_conn.unbind()
                self.create_home_directory()
            else:
                helper.send_email(self.userName,
                                  LDAPActionNames.ADD_NEW_USER_TO_UGRAD,
                                  LDAPEmailBody.ADD_NEW_USER_TO_UGRAD)
                logger.debug(f"User:{self.userName} is not added to Ugrad group")
        except Exception as ex:
            helper.send_email(self.userName,
                              LDAPActionNames.ERROR_ADD_NEW_USER_TO_UGRAD,
                              LDAPEmailBody.ERROR_ADD_NEW_USER_TO_UGRAD, str(ex))
            logger.error(f"Error in Adding new User to Undergrad Group. user_name: {self.userName}", ex)

    def create_home_directory(self):
        try:
            rc = RemoteConnect()
            rc.execute_command(f"sudo python3 /srv/home_directory.py -username {self.userName} -uid {self.uidNumber}")
            # subprocess.call(["sudo", "python3", "/srv/staging/CS_Portal/home_directory.py",
            #                  "-username", self.userName, "-uid", str(self.uidNumber)])
            helper.send_email(self.userName,
                              LDAPActionNames.NEW_USER_CREATED,
                              LDAPEmailBody.NEW_USER_CREATED)
        except Exception as ex:
            helper.send_email(self.userName,
                              LDAPActionNames.ERROR_NEW_USER_CREATED,
                              LDAPEmailBody.ERROR_NEW_USER_CREATED, str(ex))
            logger.error(ex)

    def get_ldap_users(self):
        # provide a uidNumber to search for. '*" to fetch all users/groups
        search_filter = '(&(objectClass=user)(sAMAccountName=*))'

        # Establish connection to the server
        ldap_conn = self.connect_ldap_server()

        try:
            entry_generator = ldap_conn.extend.standard.paged_search(search_base='ou=People,dc=winpcs,dc=cs,dc=umb,dc=edu',
                                                                     search_filter=search_filter,
                                                                     search_scope=SUBTREE,
                                                                     get_operational_attributes=True,
                                                                     attributes=['uidNumber'],
                                                                     paged_size=1000,
                                                                     generator=True)
            maxID = 0
            for entry in entry_generator:
                currentID = entry['attributes']["uidNumber"]
                if currentID > maxID:
                    maxID = currentID
            return maxID + 1
        except Exception as ex:
            print(f"Error in fetching UID. user_name: {self.userName}", ex)

    def get_ldap_users3(self):
        f = open("/myfile","r")
        maxid= f.readline()
        f.close()
        maxuid=int(maxid)
        maxuid=maxuid+1
        f=open("/myfile","w")
        f.write(str(maxuid))
        f.close()
        return maxuid

    # def get_ldap_users3(self):
    #     file_path = r"C:\Users\kisha\portal_workspace\myfile"
        
    #     with open(file_path, "r") as f:
    #         maxid = f.readline()

    #     maxuid = int(maxid) + 1

    #     with open(file_path, "w") as f:
    #         f.write(str(maxuid))

    #     return maxuid
    
    # def get_ldap_users(self):
    #     # Provide a search base to search for.
    #     search_base = "ou=People,dc=cs,dc=local"
    #     # provide a uidNumber to search for. '*" to fetch all users/groups
    #     search_filter = "(cn=*)"
    #
    #     # Establish connection to the server
    #     ldap_conn = self.connect_ldap_server()
    #
    #     try:
    #         # only the attributes specified will be returned
    #         ldap_conn.search(
    #             search_base=search_base,
    #             search_filter=search_filter,
    #             attributes=["cn", "sn", "uid", "uidNumber"],
    #         )
    #         # search will not return any values.
    #         # the entries method in connection object returns the results
    #         users = ldap_conn.entries
    #         maxID = 0
    #         for user in users:
    #             currentUidNumber = user["uidNumber"].value
    #             if currentUidNumber is not None and currentUidNumber > maxID:
    #                 maxID = currentUidNumber
    #         return maxID + 1
    #     except Exception as ex:
    #         print(f"Error in fetching UID. user_name: {self.userName}", ex)