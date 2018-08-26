FROM ubuntu:16.04

EXPOSE 3979 5000 5001 9001

# Install dependencies
RUN dpkg --add-architecture i386
RUN apt update -y
RUN DEBIAN_FRONTEND=noninteractive apt install -y postfix
RUN apt install -y mailutils curl wget file bzip2 gzip unzip bsdmainutils python util-linux ca-certificates binutils bc tmux lib32gcc1 libstdc++6 libstdc++6:i386 git python python-pip
RUN pip install supervisor # Installing supervisord
RUN pip install gunicorn # Installing supervisord

# Clone the server agent project
RUN git clone https://github.com/badock/server_frontend.git
# ADD server_frontend server_frontend
RUN pip install -r server_frontend/requirements.txt

# Configure supervisord
ADD supervisord.conf /etc/supervisord.conf
COPY server_frontend.conf /etc/server_frontend.conf
RUN chmod 666 /etc/server_frontend.conf

CMD supervisord -n

RUN wget https://binaries.openttd.org/releases/1.7.1-RC1/openttd-1.7.1-RC1-linux-ubuntu-trusty-amd64.deb
RUN apt-get install -y gdebi
RUN wget http://security.ubuntu.com/ubuntu/pool/main/i/icu/libicu52_52.1-3ubuntu0.8_amd64.deb
RUN apt install -y ./libicu52_52.1-3ubuntu0.8_amd64.deb
RUN apt install -y ./openttd-1.7.1-RC1-linux-ubuntu-trusty-amd64.deb

CMD ["./start-openttd.sh"]
