#!/usr/bin/env bash

echo "Launching the GamingFog system"

SCREEN_NAME="gaming_fog"

##########################################################
# Cleaning existing screens
##########################################################
screen -X -S $SCREEN_NAME quit || true

##########################################################
# Cleaning existing screens
##########################################################
ps aux | grep "python *GamingFog.py" | grep -v "grep" | awk '{ print $2 }' | xargs kill -9
ps aux | grep "python *pdus_crawler.py" | grep -v "grep" | awk '{ print $2 }' | xargs kill -9

if [ "$1" != "kill" ]; then

    ##########################################################
    # Configure a screen
    ##########################################################
    COMMON_SCREEN_ARGS="-S $SCREEN_NAME -X screen"
    screen -AdmS $SCREEN_NAME

    ##########################################################
    # Launching redis
    ##########################################################
    screen $COMMON_SCREEN_ARGS -t redis bash -c "redis-server"

    ##########################################################
    # Download python dependencies
    ##########################################################
    pip install -r requirements.txt

    ##########################################################
    # Launching web application (webapp)
    ##########################################################
    screen $COMMON_SCREEN_ARGS -t gaming_fog bash -c "python GamingFog.py"
    pip install -r requirements.txt

    ##########################################################
    # Launching celery beat
    ##########################################################
    screen $COMMON_SCREEN_ARGS -t celery_beat bash -c "celery -A celery_tasks beat -l info"

    ##########################################################
    # Launching celery worker
    ##########################################################
    screen $COMMON_SCREEN_ARGS -t celery_worker bash -c "celery -A celery_tasks worker"
fi

exit 0