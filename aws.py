import boto
import args
import ConfigParser # for NoOption and NoSection exceptions

try:
	ec2 = boto.connect_ec2(aws_access_key=args.get('local_access_key', section='local'),
							aws_secret_access_key=args.get('local_secret_key', section='local'))
except ConfigParser.NoOptionError, ConfigParser.NoSectionError:
	ec2 = boto.connect_ec2()

try:
	s3 = boto.connect_s3(aws_access_key=args.get('local_access_key', section='local'),
							aws_secret_access_key=args.get('local_secret_key', section='local'))
except ConfigParser.NoOptionError, ConfigParser.NoSectionError:
	s3 = boto.connect_s3()

