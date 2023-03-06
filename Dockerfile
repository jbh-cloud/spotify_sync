FROM python:3.8-slim-buster

#Set Environment Vars for docker
ENV arl=xxx 
ENV	spot_id=x  
ENV	spot_secret=x 
ENV	spot_username=**None** 
#minute wait 
ENV	wait_time=10
    #	DiscordBotToken = **None** \ 
	#CHANNEL = **None** 

EXPOSE 9090
RUN mkdir /download
RUN mkdir /app
RUN mkdir /root/.config/spotify_sync -p

COPY config.json /app
COPY startup.sh /app

WORKDIR /app
RUN chmod +x startup.sh
# install spot_sync from requirements 
RUN pip3 install --no-cache-dir --upgrade pip && pip install -U spot_sync --no-cache-dir 

# cmd to run container at start
CMD ["/bin/bash", "/app/startup.sh"]
#CMD ["/bin/bash"]

# docker build --pull --rm -f "Dockerfile" -t spotifysync:0.3.1 "." --no-cache
# docker run -it --name spotifysync --rm  -v /home/user/Schreibtisch/tempp:/root/.config/spotify_sync  spotifysync:0.3.1 
# docker run -d --name spotifysync -v /home/user/Schreibtisch/tempp:/root/.config/spotify_sync  spotifysync:0.3.1
#TODO newer Python version may alpine version
#TODO set env vars in python and remove startuo.sh