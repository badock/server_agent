from flask import Flask
from flask_apscheduler import APScheduler
import logging
import flask
import subprocess
import json
import time
import re
import os
import uuid
import threading
from core.config.config_loader import find_config
import ConfigParser

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


def remove_ansi_char(text):
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)


DEBUG = True
SERVER_INFO = None
STATUS_TARGET = None


class Config(object):
    JOBS = [
        {
            'id': 'job1',
            'func': 'server_agent:update_server_info',
            'args': (),
            'trigger': 'interval',
            'seconds': 300
        }
    ]

    SCHEDULER_API_ENABLED = True


def update_server_info():
    global SERVER_INFO
    logger.info("updating server info")
    SERVER_INFO = fetch_server_info()

def update_server_info_until_status_changed():
    global STATUS_TARGET
    server_info = get_server_info()
    while server_info.get("network", {}).get("status", "UNKNOWN") != STATUS_TARGET:
        logger.info("Status is not yet set to '%s': current status is '%s'" % (STATUS_TARGET, server_info.get("network", {}).get("status", "UNKNOWN")))
        update_server_info()
        time.sleep(5)
        server_info = get_server_info()
    logger.info("done 'update_server_info_until_status_changed'")


app = Flask(__name__)
app.config.from_object(Config())

app.secret_key = "server_agent"

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


SERVER_FOLDER_PATH = "/home/csgoserver"
SERVER_CMD_PATH = "%s/csgoserver" % SERVER_FOLDER_PATH

TASKS = {}


def fetch_server_info():
    global SERVER_CMD_PATH
    cmd = "%s details" % SERVER_CMD_PATH

    proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
    stdout = proc.communicate('%s details' % SERVER_CMD_PATH)

    is_displaying_distro_details = 1
    is_displaying_storage = 2
    is_displaying_server_details = 3
    is_displaying_script_details = 4
    is_displaying_backups = 5
    is_displaying_parameters = 6
    is_displaying_ports = 7

    current_displaying_stage = 1

    result = {
        "distro": {},
        "storage": {},
        "server": {},
        "script": {},
        "backups": {},
        "parameters": {},
        "network": {},
        "ports": {}
    }

    for raw_line in stdout[0].split("\n"):
        if raw_line is not None:
            line = remove_ansi_char(raw_line)
            if "Storage" in line:
                current_displaying_stage = is_displaying_storage
            elif "Server Details" in line:
                current_displaying_stage = is_displaying_server_details
            elif "Script Details" in line:
                current_displaying_stage = is_displaying_script_details
            elif "Backups" in line:
                current_displaying_stage = is_displaying_backups
            elif "Parameters" in line:
                current_displaying_stage = is_displaying_parameters
            elif "Ports" in line:
                current_displaying_stage = is_displaying_ports

            if ":" in line:
                raw_values = line.split(":")
                key = raw_values[0].strip().replace(" ", "_").lower()
                value = ":".join([x.strip() for x in raw_values[1:]])

                if current_displaying_stage == is_displaying_distro_details:
                    result["distro"][key] = value
                elif current_displaying_stage == is_displaying_storage:
                    result["storage"][key] = value
                elif current_displaying_stage == is_displaying_server_details:
                    result["server"][key] = value
                elif current_displaying_stage == is_displaying_script_details:
                    result["script"][key] = value
                elif current_displaying_stage == is_displaying_backups:
                    result["backups"][key] = value
                elif current_displaying_stage == is_displaying_parameters:
                    result["parameters"][key] = value
                elif current_displaying_stage == is_displaying_ports:
                    result["network"][key] = value
            else:
                if current_displaying_stage == is_displaying_ports:
                    if ">" in line or "<" in line:
                        raw_values = [x for x in line.split(" ") if x != "" and x is not None]
                        port = int(raw_values[3])
                        direction = raw_values[2]
                        label = raw_values[1]
                        types = raw_values[4].split("/")

                        result["ports"][port] = {
                            "port": port,
                            "direction": direction,
                            "label": label,
                            "types": types
                        }
                else:
                    if current_displaying_stage == is_displaying_parameters and line != "":
                        result["parameters"] = line
    return result


def get_server_info():
    global SERVER_INFO
    if SERVER_INFO is None:
        SERVER_INFO = fetch_server_info()
    return SERVER_INFO


def get_console_log(num_page):
    global SERVER_FOLDER_PATH
    info = get_server_info()
    service_name = info["script"]["service_name"]

    console_log_path = "%s/log/console/%s-console.log" % (SERVER_FOLDER_PATH, service_name)
    logger.info("console_log_path: %s" % console_log_path)

    #cmd = """nline=$(cat %s | wc -l); sed -n $(($nline-100)),${nline}p %s | tac""" % (console_log_path, console_log_path)
    cmd = """cat %s """ % (console_log_path)

    proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
    stdout = proc.communicate(cmd)
    lines = stdout[0].split("\n")

    return {
        "status": "OK",
        "logfile": console_log_path,
        "content": lines
    }


def get_task_log(task_id):
    global SERVER_FOLDER_PATH
    global TASKS

    if not task_id in TASKS:
        return {
            "output": []
        }

    task = TASKS.get(task_id)

    f = open(task.get("log_file"), "r")
    lines = [remove_ansi_char(line) for line in f.readlines()]

    return {
        "output": lines
    }


def server_start():
    global SERVER_CMD_PATH
    global TASKS

    task_uuid = str(uuid.uuid4())
    tmp_log_file = "/tmp/%s.log" % (task_uuid)

    cmd = '%s start > %s 2>&1' % (SERVER_CMD_PATH, tmp_log_file)
    proc = subprocess.Popen(['/bin/bash', '-c', cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
    # stdout = proc.communicate('%s restart > /dev/null 2>&1' % SERVER_CMD_PATH)


    TASKS[task_uuid] = {
        "pid": proc.pid,
        "proc": proc,
        "action_type": "start",
        "log_file": tmp_log_file,
        "created_at": time.time()
    }

    return {
        "started": True,
        "task_id": task_uuid,
        "action_type": "start",
        "log_file": tmp_log_file
    }


def server_stop():
    global SERVER_CMD_PATH
    global TASKS

    task_uuid = str(uuid.uuid4())
    tmp_log_file = "/tmp/%s.log" % (task_uuid)

    cmd = '%s stop > %s 2>&1' % (SERVER_CMD_PATH, tmp_log_file)
    proc = subprocess.Popen(['/bin/bash', '-c', cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
    # stdout = proc.communicate('%s stop > /dev/null 2>&1' % SERVER_CMD_PATH)


    TASKS[task_uuid] = {
        "pid": proc.pid,
        "proc": proc,
        "action_type": "stop",
        "log_file": tmp_log_file,
        "created_at": time.time()
    }

    return {
        "started": True,
        "task_id": task_uuid,
        "action_type": "stop",
        "log_file": tmp_log_file
    }


def server_restart():
    global SERVER_CMD_PATH
    global TASKS

    task_uuid = str(uuid.uuid4())
    tmp_log_file = "/tmp/%s.log" % (task_uuid)

    cmd = '%s restart > %s 2>&1' % (SERVER_CMD_PATH, tmp_log_file)
    proc = subprocess.Popen(['/bin/bash', '-c', cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
    # stdout = proc.communicate('%s restart > /dev/null 2>&1' % SERVER_CMD_PATH)


    TASKS[task_uuid] = {
        "pid": proc.pid,
        "proc": proc,
        "action_type": "restart",
        "log_file": tmp_log_file,
        "created_at": time.time()
    }

    return {
        "started": True,
        "task_id": task_uuid,
        "action_type": "restart",
        "log_file": tmp_log_file
    }


def server_update():
    global SERVER_CMD_PATH
    global TASKS

    task_uuid = str(uuid.uuid4())
    tmp_log_file = "/tmp/%s.log" % (task_uuid)

    cmd = '%s update > %s 2>&1' % (SERVER_CMD_PATH, tmp_log_file)
    proc = subprocess.Popen(['/bin/bash', '-c', cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)

    TASKS[task_uuid] = {
        "pid": proc.pid,
        "proc": proc,
        "action_type": "update",
        "log_file": tmp_log_file,
        "created_at": time.time()
    }

    return {
        "started": True,
        "task_id": task_uuid,
        "action_type": "update",
        "log_file": tmp_log_file
    }


def server_contextualize(parameters):
    # global SERVER_DETAILS_INFO

    server_config_location = "/home/csgoserver/lgsm/config-lgsm/csgoserver/csgoserver.cfg"

    for (k, v) in parameters.iteritems():
        cmd = 'sed -i "s/%s=.*//g" %s' % (k, server_config_location)
        proc = subprocess.Popen(['/bin/bash', '-c', cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
        cmd = 'echo -e "\n%s=%s" >> %s' % (k, v, server_config_location)
        proc = subprocess.Popen(['/bin/bash', '-c', cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
        cmd = "grep -v '^ *$' %s > tmp && mv tmp %s" % (server_config_location, server_config_location)
        proc = subprocess.Popen(['/bin/bash', '-c', cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)

    # Contextualize config file with public address
    config_file_path = find_config()
    if config_file_path is not None:
        public_url = parameters.get("public_url")
	logger.info("writing public url '%s' in config file" % public_url)

        config = ConfigParser.SafeConfigParser()
        config.read(config_file_path)
        config.add_section('server')
        config.set('server', 'public_url', "%s" % public_url)

	for section in config.sections():
	    logger.info(section)
	    for name, value in config.items(section):
	        logger.info('  %s = %r' % (name, value))

        with open(config_file_path, 'w') as configfile:
            logger.warning("Writing config file %s" % config_file_path)
            config.write(configfile)
    else:
        logger.warn("WARNING: I could not find any config file during contextualization")

    return {
        "msg": "OK"
    }


def server_tasks():
    global TASKS
    result = {}
    for task_id, task in TASKS.iteritems():
        return_code = task.get("proc").poll()
        status = "pending"
        if return_code is not None:
            if return_code == 0:
                status = "success"
            else:
                status = "failed"

        result[task_id] = {
            "task_id": task_id,
            "action_type": task.get("action_type"),
            "status": status,
            "created_at": task.get("created_at")
        }
    return result


# SERVER_DETAILS_INFO = None


@app.route("/server/details")
def web_server_info():
    server_info = get_server_info()
    return json.dumps(server_info)


@app.route("/server/status")
def web_server_status():
    server_info = get_server_info()
    status = server_info["server"]["status"]
    return json.dumps({
        "status": status
    })


@app.route("/server/console")
def web_server_console():
    result = get_console_log()
    return json.dumps(result)


@app.route("/server/console/num_page=<int:num_page>")
def web_server_console_limit(num_page):
    result = get_console_log(num_page)
    return json.dumps(result)


@app.route("/server/tasks/<task_id>/output")
def web_server_task_log(task_id):
    result = get_task_log(task_id)
    return json.dumps(result)


@app.route("/server/start")
def web_server_start():
    @flask.after_this_request
    def after_request(response):
        global STATUS_TARGET
        STATUS_TARGET = "ONLINE"
        threading.Thread(target=update_server_info_until_status_changed).start()
        #update_server_info()
        return response
    result = server_start()
    return json.dumps({
        "action": "start",
        "result": result
    })


@app.route("/server/stop")
def web_server_stop():
    @flask.after_this_request
    def after_request(response):
        global STATUS_TARGET
        STATUS_TARGET = "OFFLINE"
        threading.Thread(target=update_server_info_until_status_changed).start()
        #update_server_info()
        return response
    result = server_stop()
    return json.dumps({
        "action": "stop",
        "result": result
    })


@app.route("/server/restart")
def web_server_restart():
    @flask.after_this_request
    def after_request(response):
        global STATUS_TARGET
        STATUS_TARGET = "ONLINE"
        threading.Thread(target=update_server_info_until_status_changed).start()
        #update_server_info()
        return response
    result = server_restart()
    return json.dumps({
        "action": "restart",
        "result": result
    })


@app.route("/server/contextualize", methods=['POST'])
def web_server_contextualize():
    contextualization_data = json.loads(flask.request.data)
    result = server_contextualize(contextualization_data)
    return json.dumps(result)


@app.route("/server/update")
def web_server_update():
    result = server_update()
    return json.dumps(result)


@app.route("/server/tasks")
def web_server_tasks():
    result = server_tasks()
    return json.dumps(result)


threading.Thread(target=update_server_info).start()

if __name__ == "__main__":
    # Run web application
    logger.info("Creating the 'server_agent' web application")
    app.jinja_env.auto_reload = DEBUG

    app.run(host="0.0.0.0", port=5000, debug=DEBUG, threaded=True)
