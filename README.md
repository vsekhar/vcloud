1.	Import your regular public ssh key into AWS for easy connection to instances
	(note the name you gave it for the credentials file)
1.	Create two S3 buckets, one to store code and one to store deploy packages
1.	Install ec2 api tools (sudo apt-get install ec2-api-tools)
1.	Copy CREDENTIALS.template to CREDENTIALS and fill it out
1.	Launch and connect to a development server with './launch -d'
1.	Check on package, see that it compiled, upload it to deploy_bucket/deploy_file
1.	Launch run nodes with './launch n' where 'n' is the number of nodes

