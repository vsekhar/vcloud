Overview
========

vcloud is a set of scripts that help with spawning EC2 machines, injecting them with code, providing them with information about the cluster, and launching user's code.

The inspiration for this code comes from [Alestic](http://alestic.com)'s concept of user-data scripts, and [Rightscale](http://rightscale.com)'s concept of ServerScripts, but much simpler and usable from a command line on any machine.

Features
========
* No local machine prerequisites (beyond the basics included in nearly all linux distros: bash, tar, bz2)

* No remote machine prerequisites (beyond the ability to ssh into a machine with public-private key). This enables bare AMIs or AMIs configured for other purposes to be used with no modification

* All setup is done in user scripts, allowing the shape and configuration of your instances to form part of your source code (e.g. if you code up an application that needs additional packages, you can add the package to the apt-get command in the launch script as part of your application code)

* Simple one-word commands control launching instances, injecting code, connecting to instances, and terminating. This allows you to rapidly experiment, spin-up machines, run code, tear down whole clusters, etc.

Instructions
============

Setting up your code and data package
------------------------------

1.	Your code and data should be placed in a folder along with a script `vcloud-launch` which will be executed on the cluster machines.

	An example folder structure is:
		my_data/
			vcloud-launch
			my_code.c
			my_data.csv
			...
	
1.	Compress the folder into a single package:
		$ tar cjhf my_data.tar.bz2 my_data/
	
	Note the name of the folder inside the package for the CREDENTIALS file later (in the example above, the package folder is `my_data`)
	

Setting up vcloud
-----------------

1.	Install prerequisites
		$ sudo apt-get install ec2-api-tools

1.	Tell `ec2-api-tools` where to find your AWS cert and private key by adding to your `.bashrc` something like:
		export EC2_PRIVATE_KEY=${HOME}/.ec2/pk-aaaaaaaaaaa.pem
		export EC2_CERT=${HOME}/.ec2/cert-aaaaaaaaaaa.pem

1.	Import your regular public ssh key into AWS for easy connection to instances (remember the `key_name` for the credentials file)
		$ ec2-import-keypair key_name --public-key-file ~/.ssh/id_rsa.pub

1.	Copy CREDENTIALS.template to CREDENTIALS and fill it out

Launching a server or cluster
-----------------------------

1.	Launch a cluster of servers using the launch script, e.g. to launch 4 servers:
		$ ./launch 4
	
	If no number of servers is specified, one server is launched by default.

1.	Inject your code and data package you prepared earlier:
		$ ./inject my_code.tar.bz2
	
	The tarball will be uncompressed, the package directory `cd`'d into, and the `vcloud-launch` script executed.

Connecting to servers in the cluster
------------------------------------

If you wish to connect to a server in the cluster to observe execution or make changes, use the `connect` script.

To connect to the first server:
		$ ./connect

To connect to another server:
		$ ./connect 3

Note that server numbering starts from 0. So the above command will connect to the fourth server.

Transferring files from a server to the local machine
-----------------------------------------------------

If you wish to transfer a file from the first server (i.e. server #0), use the `scpget` script:
		$ ./scpget remote_dir/remote_file local_dir/local_file

This is useful if you are spinning up a single server to compile your code in the remote environment (see below).

Remotely compiling code
-----------------------

You may want to compile C/C++ or other code in the remote environment.

Example folder structure for a source directory:
		my_code/
			my_src_1/
				...
			my_src_2/
				...
			vcloud-launch	# see example below
			SConstruct		# or Makefile...
			SConscript

Example `vcloud-launch` script for compilation:
		#!/bin/bash
		set -ex		# output commands and stop on errors
		exec >> /var/log/inject.log 2>&1	# logging
		date '+%Y-%m-%d %H:%M:%S'
		
		# install needed dev environment
		export DEBIAN_FRONTEND=noninteractive
		sudo apt-get -qy update && sudo apt-get -qy upgrade
		sudo apt-get -qy install g++ python-dev scons curl
		
		# build and install boost in a temp dir
		cur_dir=$( pwd )
		build_dir=$( mktemp -d )
		cd "$build_dir"
		curl -LsS -o ${boost_filename}.tar.bz2 \
			http://sourceforge.net/projects/boost/files/boost/${boost_version}/${boost_filename}.tar.bz2/download
		tar jxf ${boost_filename}.tar.bz2 && rm ${boost_filename}.tar.bz2
		cd ${boost_filename}
		./bootstrap.sh --without-libraries=$suppressed_boost_libraries --with-python-version=$python_version \
			&& sudo ./bjam -j4 -d0 install
		cd "$cur_dir"
		sudo rm -rf "$build_dir" # needs to be sudo cuz we used sudo during build
		cd "$cur_dir"
		
		# build my code
		scons

Once it is done compiling, use `scpget` to get the resulting file(s):
		$ tar cjhf my_code.tar.bz2 my_code/
		$ ./launch							# defaults to 1 machine
		$ ./inject my_code.tar.bz2
		$ sleep 10							# wait for completion of compilation
		$ ./scpget my_code/compiled_file .	# places compiled file in local directory
		$ ./terminate						# terminate the compile server

You can now place the compiled file into a package for use by your run servers and launch it across a number of servers:
		$ cp compiled_file my_data/
		$ tar cjhf my_data.tar.bz2 my_data/
		$ ./launch 10						# launch 10 run servers
		$ ./inject my_data.tar.bz2

Accessing running processes on servers
--------------------------------------

You may want to access the running processes on your servers after an `inject` command in order to monitor or interact with them in some way. This is easy because `inject` launches the remote process in a screen. You can use the `connect` command to connect to a server of your choice and attach to that screen:
		$ ./connect	1	# connect to server #1
						# server numbers start at 0, if server number is omitted, server 0 is used as default)
		uDom-123-124-125-126$ screen -r


Architecture
============

vcloud is a set of scripts that run on a local admin machine. They spawn the EC2 machines and bootstrap them with the needed software (installation packages, and bundles of code and config files).

The bootstrap software on each machine arranges for the bundles to be unpacked and executed.

A vmesh launcher will spawn a certain number of processes on the node and will try to interconnect them as seeds for each other. The number of processes launched on a node should parallel the number of cores on the machine. The memory limit given to each process will have to be small enough that all the processes using that much memory won't cause thrashing on the machine.

Each vmesh process imports vgp as a python/c++ extension module, creates a population, starts exchanging organisms, and advancing through evolution. Vmesh also responds to requests/commands as part of the admin interface (a web interface? something else?)

The vgp module stores the population and responds to commands from vmesh (create population, update parameters, checkpoint, advance). The vgp module also manages population decay/predators, etc. The vgp module also spawns a sandbox process to actually undertake execution of organisms in a protected environment.

The vgp sandbox executes organisms, calling on the vgp module to resolve references to other organisms. The sandbox independently loads data that might be needed for execution. The result of execution is passed back to the module for fitness testing (should this be done in the sandbox as well?).

