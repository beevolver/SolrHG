JAVA_HOME=$1
DELTA="hours=$2, days=$3, weeks=$4"
JAVA=`which java`
PYTHON=`which python`
UNTIL=`$PYTHON -c "from datetime import datetime, timedelta; print (datetime.now() - timedelta($DELTA)).isoformat()"`
query="<delete><query>published_at:[* TO ${UNTIL}Z]</query></delete>"
$JAVA -jar -Ddata=args $JAVA_HOME/exampledocs/post.jar "$query"