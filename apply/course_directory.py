import os
import grp
import logging
import argparse

logger = logging.getLogger(__name__)


def symlink_rel(src, dst):
    rel_path_src = os.path.relpath(src, os.path.dirname(dst))
    os.symlink(rel_path_src, dst)


def create_course_directory(user_name, course_name, semester, professor, uid, graderGroup):
    source = f'/courses/{course_name}/{semester}/{professor}/{user_name}'
    destination = f'/vol/stu/home/{user_name}/{course_name}'

    isSourceExist = os.path.exists(source)

    if not isSourceExist:
        os.makedirs(source)

    #symlink_rel(source, destination)
    os.symlink(source, destination)
    gid = grp.getgrnam(graderGroup).gr_gid
    os.chown(source, uid, gid)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # Commands for input and output
    parser.add_argument('-user', help='User Name')
    parser.add_argument('-course', help='Course Name')
    parser.add_argument('-sem', help='Semester Name')
    parser.add_argument('-prof', help='Professor Name')
    parser.add_argument('-uid', help='Ldap UID')
    parser.add_argument('-graderGroup', help='Grader Group')

    args = vars(parser.parse_args())
    username = ""
    course = ""
    sem = ""
    prof = ""
    uid = ""
    graderGroup = ""

    # Raises an Exception if input path is not specified
    if not args["user"]:
        logger.error("Username is not passed to course_directory file")
    else:
        username = args['user']

    if not args["course"]:
        logger.error("course is not passed to course_directory file")
    else:
        course = args["course"]

    if not args["sem"]:
        logger.error("semester year is not passed to course_directory file")
    else:
        sem = args["sem"]

    if not args["prof"]:
        logger.error("Professor name is not passed to course_directory file")
    else:
        prof = args["prof"]

    if not args["uid"]:
        logger.error("UID is not passed to course_directory file")
    else:
        uid = int(args["uid"])

    if not args["graderGroup"]:
        logger.error("Grader Group is not passed to course_directory file")
    else:
        graderGroup = str(args["graderGroup"])

    create_course_directory(username, course, sem, prof, uid, graderGroup)