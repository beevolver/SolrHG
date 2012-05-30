Usage:

echo 'install JDK'

wget  --no-cookies --header "Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F" "http://download.oracle.com/otn-pub/java/jdk/7u4-b20/jdk-7u4-linux-x64.tar.gz"

tar -xvf jdk-7u4-linux-x64.tar.gz

cd jdk1.7.0_04/

sudo mv jdk1.7.0_04 /usr/lib/jvm/

sudo update-alternatives --install "/usr/bin/java" "java" "/usr/lib/jvm/bin/java" 1
sudo update-alternatives --install "/usr/bin/javac" "javac" "/usr/lib/jvm/bin/javac" 1
sudo update-alternatives --install "/usr/bin/javaws" "javaws" "/usr/lib/jvm/bin/javaws" 1
sudo update-alternatives --install "/usr/bin/jps" "jps" "/usr/lib/jvm/bin/jps" 1

java -version

echo 'if Java installed successfully, move on to next step'

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
