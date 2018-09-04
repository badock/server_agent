FROM ubuntu:16.04

EXPOSE 3979 5000 5001 9001 3977

# Install dependencies
RUN dpkg --add-architecture i386
RUN apt update -y
RUN DEBIAN_FRONTEND=noninteractive apt install -y postfix
RUN apt install -y mailutils curl wget file bzip2 gzip unzip bsdmainutils python util-linux ca-certificates binutils bc tmux lib32gcc1 libstdc++6 libstdc++6:i386 git python python-pip
RUN pip install supervisor # Installing supervisord
RUN pip install gunicorn # Installing supervisord
RUN apt-get install -y gdebi
RUN wget http://security.ubuntu.com/ubuntu/pool/main/i/icu/libicu52_52.1-3ubuntu0.8_amd64.deb
RUN apt install -y ./libicu52_52.1-3ubuntu0.8_amd64.deb
RUN wget https://binaries.openttd.org/releases/1.8.0/openttd-1.8.0-linux-ubuntu-trusty-amd64.deb
RUN apt install -y ./openttd-1.8.0-linux-ubuntu-trusty-amd64.deb
RUN apt install -y screen

# Creating a systemD service for ottd
WORKDIR /root
RUN wget https://bitbucket.org/frodus/openttd-init/downloads/openttd-init-1.2.1.zip
RUN unzip openttd-init-1.2.1.zip
RUN ln -s ~/openttd-init/openttd /etc/init.d/openttd
RUN mv openttd-init/config.example openttd-init/config
RUN /bin/sed -i "s/USERNAME.*=.*/USERNAME=\"csgoserver\"/g" openttd-init/config

RUN chmod 755  ~/openttd-init/openttd
RUN sudo update-rc.d openttd defaults

# Create a csgoserver
RUN useradd -ms /bin/bash csgoserver
USER csgoserver
WORKDIR /home/csgoserver

# Install ottd

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
RUN pip install -r /home/csgoserver/server_frontend/requirements.txt

# Inject the game name the server agent's config
RUN /bin/sed -i "s/game.*=.*/game = ottd/g" /etc/server_frontend.conf
RUN /bin/sed -i "s/server_ip.*=.*/server_ip = 127.0.0.1:3979/g" /etc/server_frontend.conf

# Initialize configuration files with default values
RUN bash -c "service openttd start; service openttd stop;"
RUN /bin/sed -i "s/rcon_password.*=.*/rcon_password = password/g" /home/csgoserver/.openttd/openttd.cfg
RUN /bin/sed -i "s/admin_password.*=.*/admin_password = password/g" /home/csgoserver/.openttd/openttd.cfg

USER csgoserver
CMD supervisord -n
