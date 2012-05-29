Usage:

echo 'install JDK'

Install Apache and update the path in roll.py (EXAMPLE_PATH)
wget http://mirror.metrocast.net/apache/lucene/solr/3.5.0/apache-solr-3.5.0.tgz

sudo mv apache-solr-3.5.0.tgz /mnt

sudo chown -R ubuntu:ubuntu /mnt

cd /mnt

tar -xvf apache-solr-3.5.0.tgz 

echo 'Install python-pip, build-essential, python-dev, fabric'

To make rolling indices in solr using HourGlass, check this repo out and from solrhg directory,
$fab -i <private_key.pem> -H <host> -f roll.py make_rolling_index:<1d,1w,1m,6m>

To clean everything up, which was installed by this script
$fab -i <private_key.pem> -H <host> -f roll.py cleanup

How it works:




Design Considerations:



TO-DOs:
