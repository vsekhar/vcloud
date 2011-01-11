Setting Up
==========

1.	Import your regular public ssh key into AWS for easy connection to instances
	(note the name you gave it for the credentials file)
1.	Create two S3 buckets, one to store code and one to store deploy packages
1.	Install ec2 api tools (sudo apt-get install ec2-api-tools)
1.	Copy CREDENTIALS.template to CREDENTIALS and fill it out
1.	Launch and connect to a development server with './launch -d'
1.	Check on package, see that it compiled, upload it to deploy_bucket/deploy_file
1.	Launch run nodes with './launch n' where 'n' is the number of nodes
	(startup script will unzip the deploy_file, and use python3 to run main.py
	in a detached screen process as the 'ubuntu' user)

Architecture
============

vcloud is a set of scripts that run on a local admin machine. They spawn the EC2 machines and bootstrap them with the needed software (installation packages, and bundles of code and config files).

The bootstrap software on each machine arranges for the bundles to be unpacked and executed.

A vmesh launcher will spawn a certain number of processes on the node and will try to interconnect them as seeds for each other. The number of processes launched on a node should parallel the number of cores on the machine. The memory limit given to each process will have to be small enough that all the processes using that much memory won't cause thrashing on the machine.

Each vmesh process imports vgp as a python/c++ extension module, creates a population, starts exchanging organisms, and advancing through evolution. Vmesh also responds to requests/commands as part of the admin interface (a web interface? something else?)

The vgp module stores the population and responds to commands from vmesh (create population, update parameters, checkpoint, advance). The vgp module also manages population decay/predators, etc. The vgp module also spawns a sandbox process to actually undertake execution of organisms in a protected environment.

The vgp sandbox executes organisms, calling on the vgp module to resolve references to other organisms. The sandbox independently loads data that might be needed for execution. The result of execution is passed back to the module for fitness testing (should this be done in the sandbox as well?).

