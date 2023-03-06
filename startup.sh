#!/bin/bash

output=$(spotify_sync config  list-paths  | tail -c 7)
# cehck if config found 
if [ "${output}" == "-----" ];  then
  # If no profile found, run init
 spotify_sync config add myFirstProfile config.json
 spotify_sync utils authorize-spotify --profile myFirstProfile     
else
  echo "config ok"
fi


while true; do
  echo "Starting loop..."
  # try-catch block
  if spotify_sync run auto --profile myFirstProfile; then
    echo "Success!"
  else
    echo "Error occurred!"
  fi
  # wait for the specified number of minutes
  echo "Waiting for $wait_time minutes..."
  sleep "$wait_time"m
done
#./root/.config/spotify_sync
