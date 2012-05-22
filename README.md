Usage:

To make rolling indices in solr using HourGlass, check this repo out and from solrhg directory,
$fab -i <private_key.pem> -H <host> -f roll.py make_rolling_index:<1d,1w,1m,6m>

To clean everything up, which was installed by this script
$fab -i <private_key.pem> -H <host> -f roll.py cleanup

How it works:




Design Considerations:



TO-DOs:
