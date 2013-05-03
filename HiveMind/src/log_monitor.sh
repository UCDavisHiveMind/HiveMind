#!/bin/bash

#-
#- monitors the hivemind log file for activity of interest
#- command line argument
#-   log_monitor.py   :: show only "alerts"
#-   log_monitor.py 0 :: show only errors
#-   log_monitor.py 1 :: show errors and "alerts"
#-   log_monitor.py 2 :: show errors, "alerts" and "things found"
#-   log_monitor.py 3 :: show errors, "alerts", "things found" and "ant movements"
#-   log_monitor.py 4 :: show everything


X=$1

if [ -z "$X" ]; then
  S='alert:'
elif [ $X -eq 0 ]
then
  S='error|ERROR'
elif [ $X -eq 1 ]
then
  S='error|ERROR|alert:'
elif [ $X -eq 2 ]
then
  S='error|ERROR|alert:|found_something|action:'
elif [ $X -eq 3 ]
then
  S='error|ERROR|alert:|found_something|action:|ant-received'
elif [ $X -eq 4 ]
then
  S=''
else
  echo "invalid option -- "
  echo '   log_monitor.py   :: show only "alerts"'
  echo '   log_monitor.py 0 :: show only errors'
  echo '   log_monitor.py 1 :: show errors and "alerts"'
  echo '   log_monitor.py 2 :: show errors, "alerts" and "things found"'
  echo '   log_monitor.py 3 :: show errors, "alerts", "things found" and "ant movements"'
  echo '   log_monitor.py 4 :: show everything'
  exit
fi


tail -f /var/log/hivemind.log | egrep "$S"
