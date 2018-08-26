FROM ubuntu:16.04

EXPOSE 27015 5000 5001 9001

# Install dependencies
RUN dpkg --add-architecture i386
RUN apt update -y
RUN DEBIAN_FRONTEND=noninteractive apt install -y postfix
RUN apt install -y mailutils curl wget file bzip2 gzip unzip bsdmainutils python util-linux ca-certificates binutils bc tmux lib32gcc1 libstdc++6 libstdc++6:i386 git python python-pip
RUN pip install supervisor # Installing supervisord
RUN pip install gunicorn # Installing supervisord

# Create a csgoserver
RUN useradd -ms /bin/bash csgoserver
USER csgoserver
WORKDIR /home/csgoserver

# Install LinuxGameServer
RUN wget https://linuxgsm.com/dl/linuxgsm.sh
RUN chmod +x linuxgsm.sh

RUN bash linuxgsm.sh csgoserver
RUN ./csgoserver auto-install

# Inject the public IP in the server's config
RUN /bin/echo -e "\n\nip=\"0.0.0.0\"" >> /home/csgoserver/lgsm/config-lgsm/csgoserver/csgoserver.cfg

# Clone the server agent project
RUN git clone https://github.com/badock/server_frontend.git
# ADD server_frontend server_frontend
RUN pip install -r server_frontend/requirements.txt

# Configure supervisord
ADD ../conf/supervisord.conf.example /etc/supervisord.conf
COPY --chown=csgoserver server_frontend.conf /etc/server_frontend.conf
RUN chmod 666 /etc/server_frontend.conf

CMD supervisord -n
