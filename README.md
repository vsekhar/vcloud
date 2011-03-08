Overview
========

vcloud is a set of scripts that help with spawning EC2 machines, injecting them with code, providing them with information about the cluster, and launching user's code.

The inspiration for this code comes from [Alestic](http://alestic.com)'s concept of user-data scripts, and [Rightscale](http://rightscale.com)'s concept of ServerScripts, but much simpler and usable from a command line on any machine.

Features
========
* No local machine prerequisites (beyond the basics included in nearly all linux distros: bash, tar, bz2)

* No remote machine prerequisites (beyond the ability to ssh into a machine with public-private key). This enables bare AMIs or AMIs configured for other purposes to be used with no modification

* All setup is done in user scripts, allowing the shape and configuration of your instances to form part of your source code

* Simple one-word commands control launching instances, injecting code, connecting to instances, and terminating. This allows you to rapidly experiment, spin-up machines, run code, tear down whole clusters, etc.

Usage
=====

NB: This guide assumes you are running scripts from the vcloud/bin directory. Installation is not yet implemented.

Creating a deployment package
-----------------------------

Your code and data should be placed in a folder along with a script `vcloud-launch` which will be executed on the cluster machines.

An example folder structure is:
	my_deployment/
		vcloud-launch
		my_compute_kernel
		my_data.csv
		 ...
	
Deploying cluster
-----------------

1.	Launch a cluster of servers using the launch script, e.g. to launch 4 servers:
		$ ./launch 4
	
	If a number of servers is not specified, one server is launched by default.
	
	If you want to add more servers after you launched a few, just launch again:
		$ ./launch 4
		$ ./launch 2	# now 6 servers are running

1.	Inject your deployment package:
		$ ./inject my_deployment/
	
	On each machine, the deployment directory will be transferred, the directory `cd`'d into, and the `vcloud-launch` script executed.
	
	The `vcloud-launch` script can be any kind of executable ('sha-bang' scripts, binaries, etc.), but a simple bash script is recommended if your AMI is a basic server with no interpreters installed. You can then install interpreters, and launch other programs from within that script. (see `pkg/vcloud-launch` for an example script)

NB: You should not add more servers after you have injected. This is because any subsequent injections will overwrite the data from earlier ones. If processes are running using that data, they may become corrupted.
		$ ./launch 4
		$ ./inject my_deployment/
		$ ./launch 2						# now 6 servers running
											# but only 4 were injected
		$ ./inject my_deployment/			# error! initial 4 servers are corrupted

Instead, `terminate` your existing servers and re-`launch`.
	
Connecting to servers in the cluster
------------------------------------

If you wish to connect to a launched server, use the `connect` script:
		$ ./connect 0	# connect to the first server (numbering starts at 0)
		$ ./connect		# same as above, defaults to server 0
		$ ./connect 3	# connect to the *fourth* server

You may connect to servers anytime after they are `launch`ed, whether or not they have been `inject`ed.

Interacting with processes on servers
-------------------------------------

You may want to interact with the processes running on your servers after an `inject` command. To enable this, `inject` launches your `vcloud-launch` script/program in a detached [screen](http://www.manpagez.com/man/1/screen/) process. You can `connect` to a server and attach to that screen:
		$ ./connect	1	# connect to second server
		uDom-123-124-125-126$ screen -r

If you want to detach (and leave the process running), hit CTRL-A then press D.

If the `vcloud-launch` script has already completed, the `screen` process will terminate and you won't be able to attach to it:
		uDom-123-124-125-126$ screen -r
		There is no screen to be resumed.

Therefore, it is a good idea to have your `vcloud-launch` script/program perform some kind of logging so you can examine output even after the process finishes. For example, `vcloud-launch` bash script might begin with:
		#/bin/bash
		exec > >(tee vcloud-log) 2>&1 	# log stdout and stderr to 'vcloud-log'
		date '+%Y-%m-%d %H:%M:%S'		# output date (for the log)
		# execute my stuff...

See `pkg/vcloud-launch` for an example script.

Transferring files from the cluster to the local machine
--------------------------------------------------------

Use `scpget` to transfer file(s) from a server:
		$ ./scpget remote_dir/remote_file local_dir/local_file

This is useful to pull back processed data from a single server (specifically, server 0), such as compiled code or log files.

If you want to get a file from all servers, use `scpgetall`. The files from each server will be suffixed with a server number:
		$ ./scpgetall remote_dir/remote_file local_file
		$ ls
		local_file.0
		local_file.1
		local_file.2

NB: It is not easy to associate a server number with a specific server since the server numbers are based on the order AWS lists servers via its `ec2-describe-instances` command. For example, if you wanted to examine the server that produced file `local_file.2`, you might try
		$ ./connect 2
and it would get you to the right server most of the time. But there's no guarantee. To fix this, your code could get the public hostname of the instance via its metadata and include that somehow in the data you pull back with `scpgetall`.

Remotely compiling code (manually)
----------------------------------

You may want to compile C/C++ or other code in the same remote environment in which it will eventually be run. You can do this by `inject`ing your development tree as a package just as you would a deployment package.

Example folder structure for a source directory:
		my_code/
			my_src_1/
				code1.c
				 ...
			my_src_2/
				code2.c
				 ...
			SConstruct		# or Makefile...
			SConscript

Launch, inject and connect. Your code will be in the home directory. You can then install a dev environment, build your code, and pull it back to your local machine:
		$ ./mkpkg my_code/
		$ ./launch
		$ ./inject my_code.tar.bz2
		$ ./connect
		domU124-232-231-113$ sudo apt-get -qqy install g++ python-dev scons
		 ...
		domU124-232-231-113$ cd my_code/
		domU124-232-231-113$ scons
		 ...
		domU124-232-231-113$ exit
		$ ./scpget compiled_file .
		$ ./terminate

You can then include the compiled file in your deployment package, re-package and launch the cluster:
		$ cp compiled_file my_deployment/
		$ ./launch 10						# launch 10 deployment servers
		$ ./inject my_deployment/

Remotely compiling code (automatically)
---------------------------------------

Manually setting up the remote dev environment and launching compilation can get tedious. Instead, as with deployment packages, you can insert a `vcloud-launch` script into your development package to automatically start installing and building as soon as the package is `inject`ed.

Using the directory structure from the previous section, we would have:
		my_code/
			my_src_1/
				code1.c
				 ...
			my_src_2/
				code2.c
				 ...
			SConstruct
			SConscript
			vcloud-launch	# add this for automatic build (must be executable)

(See the `dev-pkg/vcloud-launch` file for an example script that installs some development packages, builds and installs a recent version of the boost libraries, and starts building the user's code.)

Launch a server and inject (compilation will be started automatically):
		$ ./launch							# defaults to 1 machine
		$ ./inject my_code/

If you want to observe the compilation, connect to the instance and re-attach to screen (assuming compilation is still in progress):
		$ ./connect		# defaults to server 0
		domU124-232-231-113$ screen -r

The example script `dev-pkg/vcloud-launch` logs to `vcloud-log`. We can examine the log file by either connecting
		$ ./connect
		domU124-232-231-113$ less vcloud-log
or by pulling down the log file to the local machine
		$ ./scpget vcloud-log .
		$ less vcloud-log
		
Finally, we can get the compiled file(s)
		$ ./scpget my_code/compiled_file .
		$ ./terminate
and include it in our deployment package to launch a cluster as before:
		$ cp compiled_file my_deployment/
		$ ./launch 10						# launch 10 run servers
		$ ./inject my_deployment/

Configuration
=============

1.	Install prerequisites
		$ sudo apt-get install ec2-api-tools

1.	Download your x.509 and private key from the AWS security credentials webpage. Place them in a safe place (usually `~/.ec2/`)

1.	Generate an RSA ssh key if you don't already have one using `ssh-keygen`. Remember where the public key is stored (usually `~/.ssh/id_rsa.pub`)

1.	Configure environment variables, most easily done by putting the following in your `.bashrc` file:
		export EC2_PRIVATE_KEY=${HOME}/.ec2/pk-aaaaaaaaaaa.pem	# downloaded above
		export EC2_CERT=${HOME}/.ec2/cert-aaaaaaaaaaa.pem		# downloaded above
		export VCLOUD_KEY_NAME=key_name
		export VCLOUD_SECURITY_GROUP=ClusterGroup
		export VCLOUD_AIM=ami-ccf405a5							# Alestic Ubuntu 10.10 Maverick 32-bit
		export VCLOUD_LOGIN_USER=ubuntu

1.	Import your ssh key into AWS
		$ ec2-import-keypair $VCLOUD_KEY_NAME --public-key-file ~/.ssh/id_rsa.pub
	
1.	Create a security group for your cluster (see [EC2 documentation](http://docs.amazonwebservices.com/AWSEC2/latest/CommandLineReference/))

	For example, to allow instances to communicate with each other on port 10240:
		$ ec2-add-group $VCLOUD_SECURITY_GROUP -d "this is the group for the clusters"
		$ ec2-authorize $VCLOUD_SECURITY_GROUP --source-group $VCLOUD_SECURITY_GROUP -p 10240

	NB: launched machines will be part of the 'default' security group as well as the one you specify with `$VCLOUD_SECURITY_GROUP`. The 'default' group usually just allows ssh on port 22 (which is needed for injection).
