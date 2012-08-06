Usage:

To make rolling indices in solr using HourGlass, check this repo out and from solrhg directory,
$fab -i <private_key.pem> -H <user>@<host> -f roll.py make_rolling_index:1d,1w,1m,6m

To clean everything up, which was installed by this script
$fab -i <private_key.pem> -H <user>@<host> -f roll.py cleanup

Before running the fab command, do the following on the server,

    1. Make sure that the line starting with "cron.*  " in /etc/rsyslog.d/50-default.conf is NOT commented, so that we get to see the cron logs in /var/log/cron.log
    2. apt-get install build-essential python-dev python-pip
        pip install fabric
    3. Change the default settings of USER (default: beeadmin), PATH(default:/solr/apache-solr-3.5.0) etc in config.py.


--
--
echo 'Add User beeadmin'

useradd -m beeadmin
passwd beeadmin

echo 'Add beeadmin to sudoers file'
echo 'beeadmin    ALL=(ALL:ALL) ALL <- ADD THIS TO SUDOERS FILE'

visudo

echo 'Copy over the id_rsa.pub from .ssh to the server'

echo 'scp ~/.ssh/id_rsa.pub beeadmin@<IP>'

echo 'Login to server and create .ssh directory and copy over the id_rsa.pub to authorized_keys'

echo 'Install Sun JDK 1.6+'

wget  --no-cookies --header "Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F" "http://download.oracle.com/otn-pub/java/jdk/7u4-b20/jdk-7u4-linux-x64.tar.gz"

tar -xvf jdk-7u4-linux-x64.tar.gz

cd jdk1.7.0_04/

sudo mv jdk1.7.0_04 /usr/lib/jvm/

sudo update-alternatives --install "/usr/bin/java" "java" "/usr/lib/jvm/bin/java" 1
sudo update-alternatives --install "/usr/bin/javac" "javac" "/usr/lib/jvm/bin/javac" 1
sudo update-alternatives --install "/usr/bin/javaws" "javaws" "/usr/lib/jvm/bin/javaws" 1
sudo update-alternatives --install "/usr/bin/jps" "jps" "/usr/lib/jvm/bin/jps" 1

java -version

echo 'If Sun Java installed successfully, move on to next step'

Install Apache and update the path in roll.py (EXAMPLE_PATH)
wget http://mirror.metrocast.net/apache/lucene/solr/3.5.0/apache-solr-3.5.0.tgz

sudo mv apache-solr-3.5.0.tgz /solr

sudo chown -R beeadmin:beeadmin /solr

cd /solr

tar -xvf apache-solr-3.5.0.tgz 

echo 'Install python-pip, build-essential, python-dev, fabric'


--------------------------
Manual merge: Assuming that the EXAMPLE_PATH is /solr/apache-solr-3.5.0/

classpath=/solr/apache-solr-3.5.0/solr_1d/solr/lib
java -cp $classpath/lucene-core-3.5.0.jar:$classpath/lucene-misc-3.5.0.jar org/apache/lucene/misc/IndexMergeTool /path/to/newindex /path/to/index1 /path/to/index2

/solr/apache-solr-3.5.0/solr_1w/solr/data/index/

For example, to merge 1w slice with a 1m slice, you do
EXAMPLE_PATH=/solr/apache-solr-3.5.0
java -cp $classpath/lucene-core-3.5.0.jar:$classpath/lucene-misc-3.5.0.jar org/apache/lucene/misc/IndexMergeTool $EXAMPLE_PATH/solr_1m/solr/data/index/  $EXAMPLE_PATH/solr_1m/solr/data/index/  $EXAMPLE_PATH/solr_1w/solr/data/index/  

and delete the index at $EXAMPLE_PATH/solr_1w/solr/data/index/  and restart both solr_1w and solr_1m

