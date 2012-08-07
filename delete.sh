PORT=$1
DELTA="hours=$2, days=$3, weeks=$4"
PYTHON=`which python`
UNTIL=`$PYTHON -c "from datetime import datetime, timedelta; print (datetime.now() - timedelta($DELTA)).isoformat()"`
query="<delete><query>published_at:[* TO ${UNTIL}Z]</query></delete>"
echo "deleting all the old ones now..."
date

curl http://127.0.0.1:$PORT/solr/update/?commit=true -H "Content-Type: text/xml" --data-binary "$query"

date
echo "successfully deleted all the old ones now..."
