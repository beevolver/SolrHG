# upstart script generator to daemonize solr
# usage: bash solr.conf.sh /path/to/solr/home

SOLR_HOME=$1
cat<<END
# upstart script to daemonize solr
# to be placed in /etc/init after replacing SOLR_HOME appropriately.
# usage: service solr-xxx [start|stop], if this is renamed to solr-xxx in /etc/init dir.
description "Solr Search Server"

# Make sure the file system and network devices have started before
# begin the daemon
start on (filesystem and net-device-up IFACE!=lo)

# Stop the event daemon on system shutdown
stop on shutdown

# Respawn the process on unexpected termination
respawn

exec /usr/bin/java -Dsolr.solr.home=$SOLR_HOME/solr -Djetty.home=$SOLR_HOME -jar $SOLR_HOME/start.jar
END
