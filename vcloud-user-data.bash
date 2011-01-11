# no sha-bang since this needs credentials added at the top to work
# (see the 'launch' script)

###############################################################################
#
# This user-data script, executed by many EC2 AMI's (including Alestic.com's
# Ubuntu AMI's) can either load and compile code, or load and execute code.
#
# Deploy Mode:
#	1) Load tarball s3://deploy_bucket/deploy_file (must be publicly readable)
#
#		NB: deploy_bucket should disallow file listings by "Everyone," but
#			should allow file downloading; then an obfuscated name for
#			deploy_file can prevent randoms from downloading it
#
#	2) Unzip tarball and execute with python3 and the instance parameters:
#
#		python3 main.py --checkpoint-dir="$local_mnt_dir" \
#			--hostname=$dns_name --my-index=$index --data_bucket=$data_bucket
#
#	3) Exit and wait for ssh
#
#		NB: attach to process from step 2 with 'screen -r' from user 'ubuntu'
#
# Development Mode:
#	1) Load tarball s3://deploy_bucket/code_file (must be publicly readable)
#
#	2) Unzip tarball and build with Scons:
#
#		scons -j4 
#
#	3) Exit and wait for ssh
#
###############################################################################


# run parameters
base_packages="curl python python3 screen"
local_mnt_dir=/mnt

# dev parameters
dev_packages="python-dev python3-dev g++ libbz2-dev zlib1g-dev scons"
python_version=3.1
boost_version=1.45.0
boost_version_uscr=`echo $boost_version | sed 's/\./_/g'`
boost_filename=boost_$boost_version_uscr
suppressed_boost_libraries=date_time,regex,filesystem,graph,graph_parallel,iostreams,math,mpi,program_options,signals,system,test,wave

set -ex
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

export DEBIAN_FRONTEND=noninteractive
date '+%Y-%m-%d %H:%M:%S'
sudo apt-get -qy update && sudo apt-get -qy upgrade
sudo apt-get -qy install $base_packages

# prepare development environment
if [ ! -z $development ] ; then
	sudo apt-get -qy install $dev_packages
	cur_dir=$( pwd )
	
	# build and install boost
	build_dir=$( mktemp -d )
	cd "$build_dir"
	curl -LsS -o ${boost_filename}.tar.bz2 \
		http://sourceforge.net/projects/boost/files/boost/${boost_version}/${boost_filename}.tar.bz2/download
	tar jxf ${boost_filename}.tar.bz2
	rm ${boost_filename}.tar.bz2
	cd ${boost_filename}
	./bootstrap.sh --without-libraries=$suppressed_boost_libraries --with-python-version=$python_version \
		&& sudo ./bjam -j4 -d0 install
	cd "$cur_dir"
	sudo rm -rf "$build_dir" # needs to be sudo cuz we used sudo during build
	
	# get our code
	code_dir=$( mktemp -d )
	cd "$code_dir"
	curl -sS -o "code.tar.bz2" https://s3.amazonaws.com/${deploy_bucket}/${code_file} \
		&& tar jxf code.tar.bz2 && scons -j4
	# todo: package it up into a file (and upload?)
	cd "$cur_dir"

	# quit and wait for ssh
	exit
fi

# get instance metadata
metadata=http://instance-data/latest/meta-data
dns_name=`curl ${metadata}/public-hostname` #resolves to internal ip within AWS
index=`curl ${metadata}/ami-launch-index`
echo dns_name: $dns_name
echo index: $index

# set up our code
deploy_dir=$( mktemp -d )
cur_dir=$( pwd )
cd "$deploy_dir"
curl -OsS https://s3.amazonaws.com/${deploy_bucket}/${deploy_file} -o "deploy.tar.bz2" \
	&& tar jxf deploy.tar.bz2

# run inside a screen as ubuntu
su -c "screen -d -m python3 main.py --checkpoint-dir=$local_mnt_dir \
	--hostname=$dns_name --index=$index --data_bucket=$data_bucket" ubuntu

echo "user-data script completed"

