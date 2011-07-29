#
# VMESH Credentials File
#
# 1. fill out required fields, enclosing strings in quotes
# 2. rename file 'CREDENTIALS.py' and place in same directory as cloudlaunch.py
#


# AWS credentials to use to access package file. These credentials are also
# passed to the package script via the commandline:
#
#   $ <script> --access-key=<access key> --secret-key=<secret key>
#
access_key = ''
secret_key = ''

# S3 bucket and package file to download
#   - bucket and package must be accessible using the above credentials
#   - package file must be in tar-gzip format
#
# E.g.
#   bucket = 'vmesh_bucket'
#   package = 'vmesh_startup.tar.gz'
#
bucket = ''
package = ''

# Name of script inside package to run on startup
#    - optional path can be specified relative to the root of the package
#    - script must be executable: chmod +x <script>
#
# E.g.
#   Script in package root:		script = 'vmesh-launch.py'
#   Script in subdir:			script = 'pkg_subdir/vmesh-launch.py'
#
script = ''

# User to 
#    - user must exist on instance AMI (suggest 'ubuntu' for Ubuntu AMIs)
#    - package will be downloaded into user's homedir and script started
#      in a detached 'screen' belonging to this user
#
user = ''

