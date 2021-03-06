# upstart script generator to daemonize solr
# usage: bash solr.conf.sh /path/to/solr/home

SOLR_HOME=$1
MEM=$2
POST_STOP_HG=${3}
LOG_FILE="/var/log/`basename $SOLR_HOME`"
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

exec /usr/bin/java -mx${MEM} -Dsolr.solr.home=$SOLR_HOME/solr -Djetty.home=$SOLR_HOME -Dorg.mortbay.jetty.webapp.parentLoaderPriority=true -jar $SOLR_HOME/start.jar >> $LOG_FILE 2>&1

post-stop script
    # nothing will be there below to execute on a non-HG solr
if [ "$POST_STOP_HG" ]; then
    # merge the index created by the HG, with the next slice whenever it's stopped
    date
    echo "after HG is stopped, doing the merge" >> $LOG_FILE 2>&1
    $POST_STOP_HG
    date
    echo "done with the merge during post-stop" >>  /solr/apache-solr-3.5.0/solrhg.log 2>&1
fi
end script

END
