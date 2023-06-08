import os
import argparse
import logging

logger = logging.getLogger(__name__)


def create_home_directory(user_name, uid):
    path = f"/home/{user_name}"

    isExist = os.path.exists(path)

    if not isExist:
        os.makedirs(path)
        os.chown(path, uid, 10241)
        logger.debug(f"Home Directory is created for {user_name}")
    else:
        logger.error(f"User already exists in home directory. user_name: {user_name}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # Commands for input and output
    parser.add_argument('-username', help='User Name')
    parser.add_argument('-uid', help='Ldap UID')

    args = vars(parser.parse_args())
    username = ""
    uid = ""

    # Raises an Exception if input path is not specified
    if not args["username"]:
        logger.error("Username is not passed to home_directory file")
    else:
        username = args['username']

    if not args["uid"]:
        logger.error("UID is not passed to home_directory file")
    else:
        uid = int(args["uid"])

    create_home_directory(username, uid)