class ActionNames:
    EmailSubject = "CS Portal Account Activation Link."


class LDAPActionNames:
    ADD_NEW_USER = "Error in Creating new user in AD"
    USER_EXISTS = "Unable to Create new User in AD"
    SET_NEW_USER_PASSWORD = "Unable to Set Password in AD"
    ERROR_NEW_USER_PASSWORD = "Error in setting Password in AD for new USER"
    SET_NEW_USER_ATTRIBUTES = "Unable to set AD attributes for New User"
    ERROR_NEW_USER_ATTRIBUTES = "Error in Setting AD attributes (New User)"
    ADD_NEW_USER_TO_UGRAD = "Unable to add New User to UnderGrad Group"
    ERROR_ADD_NEW_USER_TO_UGRAD = "Error in Adding New User to UnderGrad Group"
    CHANGE_PASSWORD = "Error in Changing AD password"
    UNLOCK_ACCOUNT = "Unable to Unlock AD Account"
    ERROR_UNLOCK_ACCOUNT = "Error in Unlocking AD Account"
    PASSWORD_CHANGED = "Password Changed in AD"
    NEW_USER_CREATED = "New User is registered in Portal & Home Directory is created"
    ERROR_NEW_USER_CREATED = "Error in Creating Home Directory"
    ADD_USER_TO_COURSE = "Unable to add user to Course in AD"
    ERROR_ADD_USER_TO_COURSE = "ERROR in Adding user to Course in AD"
    ERROR_CHANGE_PASSWORD = "ERROR Changing Password in AD"


class LDAPEmailBody:
    USER_EXISTS = "Unable to Create new User in AD (user might already exist)"
    SET_NEW_USER_PASSWORD = "Unable to Set Password in AD"
    ERROR_NEW_USER_PASSWORD = "Error in setting Password in AD for new USER"
    SET_NEW_USER_ATTRIBUTES = "Unable to set AD attributes for New User"
    ERROR_NEW_USER_ATTRIBUTES = "Error in Setting AD attributes (New User)"
    ADD_NEW_USER_TO_UGRAD = "Unable to add New User to UnderGrad Group"
    ERROR_ADD_NEW_USER_TO_UGRAD = "Error in Adding New User to UnderGrad Group"
    NEW_USER_CREATED = "New User is registered in Portal & Home Directory is created"
    ERROR_NEW_USER_CREATED = "New User is added to AD but unable to create Home Directory"
    UNLOCK_ACCOUNT = "Unable to Unlock AD Account"
    ERROR_UNLOCK_ACCOUNT = "Error in Unlocking AD Account"
    ADD_USER_TO_COURSE = "Unable to add user to Course in AD"
    ERROR_ADD_USER_TO_COURSE = "ERROR in Adding user to Course in AD"
    ERROR_CHANGE_PASSWORD = "ERROR Changing Password in AD"


class EmailHelper:
    EMAIL_HOST = "mx1.cs.umb.edu"
    EMAIL_PORT = 25