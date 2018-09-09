FROM ubuntu:16.04

EXPOSE 27015 5000 5001 9001

# Install dependencies
RUN dpkg --add-architecture i386
RUN apt update -y
RUN DEBIAN_FRONTEND=noninteractive apt install -y postfix
RUN apt install -y mailutils curl wget file bzip2 gzip unzip bsdmainutils python util-linux ca-certificates binutils bc tmux lib32gcc1 libstdc++6 libstdc++6:i386 git python python-pip
RUN apt install -y jq openjdk-8-jre-headless
RUN pip install supervisor # Installing supervisord
RUN pip install gunicorn # Installing supervisord

# Create a csgoserver
RUN useradd -ms /bin/bash csgoserver
USER csgoserver
WORKDIR /home/csgoserver

# Install LinuxGameServer
RUN wget https://linuxgsm.com/dl/linuxgsm.sh
RUN chmod +x linuxgsm.sh

RUN bash linuxgsm.sh mcserver
RUN ./mcserver auto-install

# Clone the server agent project
RUN git clone https://github.com/badock/server_frontend.git

# ADD server_frontend server_frontend
RUN pip install -r server_frontend/requirements.txt

# Configure supervisord
USER root
RUN apt install -y nano
RUN cp server_frontend/conf/supervisord.conf.example /etc/supervisord.conf
RUN chmod 666 /etc/supervisord.conf
RUN cp server_frontend/conf/server_frontend.conf.example /etc/server_frontend.conf
RUN chmod 666 /etc/server_frontend.conf

# Inject the game name the server agent's config
RUN /bin/sed -i "s/game.*=.*/game = minecraft/g" /etc/server_frontend.conf

USER csgoserver
CMD supervisord -n
