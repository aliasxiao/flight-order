#!/bin/bash
DEBUG=1
if [ $DEBUG == 1 ]
then
  echo "gen data!"
  python gen_data.py
fi


while true
  do
      sleep 10
      num=`ps -ef | grep "python run.py" | grep -v daemon| grep -v grep |wc -l`
      if [ "$num" -gt 0 ]
      then
          echo "service is ddrunning"
      else
        python run.py
      fi
  done

