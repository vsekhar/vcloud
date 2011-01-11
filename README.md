Instructions
============

Setting up
----------

1.	Install `ec2-api-tools` and `s3cmd`
		$ sudo apt-get install ec2-api-tools s3cmd

1.	Tell `ec2-api-tools` where to find your AWS cert and private key by adding to your `.bashrc` something like:
		export EC2_PRIVATE_KEY=${HOME}/.ec2/pk-52a7d7892f31482984054b6222196bd0.pem
		export EC2_CERT=${HOME}/.ec2/cert-52a7d7892f31482984054b6222196bd0.pem

1.	Import your regular public ssh key into AWS for easy connection to instances (note the `key_name` for the credentials file)
		$ ec2-import-keypair key_name --public-key-file key_file

1.	Give `s3cmd` your AWS access credentials by writing to `${HOME}/.s3cmd`:
		[default]
		access_key={access key here}
		secret_key={secret key here}
	Or let `s3cmd` create your config file:
		$ s3cmd --configure

1.	Create two S3 buckets, one to store code and one to store deploy packages (remember these for credentials file)
		$ s3cmd mb s3://my-code-bucket
		$ s3cmd mb s3://my-deploy-bucket

1.	Copy CREDENTIALS.template to CREDENTIALS and fill it out

Compile on a development server
-------------------------------
1.	Launch and connect to a development server with `./launch -d`
1.	Check on package, see that it compiled, upload it to `my-deploy-bucket/deploy_file`
1.	[TBD: more to go here]

Launch a cluster
----------------

1.	Launch run nodes with `./launch n` where 'n' is the number of nodes. The node startup script will unpack the `deploy_file` and launch it as the `ubuntu` user with various instance-specific values. The actual launch line is:
		$ su -c "screen -d -m python3 main.py --checkpoint-dir=$local_mnt_dir \
			--hostname=$dns_name --index=$index --data_bucket=$data_bucket" ubuntu
	The script will list the public hostnames of the instances that were launched.

1.	You can check on the running process by connecting to the host and attaching to the screen:
		$ ssh ubuntu@aws-public-host-name
		remote$ screen -r

Architecture
============

vcloud is a set of scripts that run on a local admin machine. They spawn the EC2 machines and bootstrap them with the needed software (installation packages, and bundles of code and config files).

The bootstrap software on each machine arranges for the bundles to be unpacked and executed.

A vmesh launcher will spawn a certain number of processes on the node and will try to interconnect them as seeds for each other. The number of processes launched on a node should parallel the number of cores on the machine. The memory limit given to each process will have to be small enough that all the processes using that much memory won't cause thrashing on the machine.

Each vmesh process imports vgp as a python/c++ extension module, creates a population, starts exchanging organisms, and advancing through evolution. Vmesh also responds to requests/commands as part of the admin interface (a web interface? something else?)

The vgp module stores the population and responds to commands from vmesh (create population, update parameters, checkpoint, advance). The vgp module also manages population decay/predators, etc. The vgp module also spawns a sandbox process to actually undertake execution of organisms in a protected environment.

The vgp sandbox executes organisms, calling on the vgp module to resolve references to other organisms. The sandbox independently loads data that might be needed for execution. The result of execution is passed back to the module for fitness testing (should this be done in the sandbox as well?).

