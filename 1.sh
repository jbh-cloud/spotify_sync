while true; do
  echo "Starting loop..."
  # try-catch block
  if spotify_sync run auto --profile myFirstProfile; then
    echo "Success!"
  else
    echo "Error occurred!"
  fi
  # wait for the specified number of minutes
  #echo "Waiting for $WAIT_TIME minutes..."
  echo "$wait_time"m
  sleep "$wait_time"m
done