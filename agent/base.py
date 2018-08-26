from flask import Flask
from flask_apscheduler import APScheduler
import logging
import flask
import json
import time
import threading
from agent_actions import AgentActions
from core.config.config_loader import load_config
from agent.agent_actions import instantiate_agent_actions

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

game_name = load_config().get("server_agent", {}).get("game")
server_actions = instantiate_agent_actions(game_name)  # type: AgentActions

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
    logger.info("updating server info")
    server_actions.server_info = server_actions.fetch_server_info()


def update_server_info_until_status_changed():
    global STATUS_TARGET
    server_info = server_actions.get_server_info()
    while server_info.get("network", {}).get("status", "UNKNOWN") != STATUS_TARGET:
        logger.info("Status is not yet set to '%s': current status is '%s'" % (
            STATUS_TARGET, server_info.get("network", {}).get("status", "UNKNOWN")))
        update_server_info()
        time.sleep(5)
        server_info = server_actions.get_server_info()
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


@app.route("/server/details")
def web_server_info():
    server_info = server_actions.get_server_info()
    return json.dumps(server_info)


@app.route("/server/status")
def web_server_status():
    server_info = server_actions.get_server_info()
    status = server_info["server"]["status"]
    return json.dumps({
        "status": status
    })


@app.route("/server/console")
def web_server_console():
    result = server_actions.get_console_log()
    return json.dumps(result)


@app.route("/server/console/num_page=<int:num_page>")
def web_server_console_limit(num_page):
    result = server_actions.get_console_log(num_page)
    return json.dumps(result)


@app.route("/server/tasks/<task_id>/output")
def web_server_task_log(task_id):
    result = server_actions.get_task_log(task_id)
    return json.dumps(result)


@app.route("/server/start")
def web_server_start():
    @flask.after_this_request
    def after_request(response):
        global STATUS_TARGET
        STATUS_TARGET = "ONLINE"
        threading.Thread(target=update_server_info_until_status_changed).start()
        return response

    result = server_actions.server_start()
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
        return response

    result = server_actions.server_stop()
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
        return response

    result = server_actions.server_restart()
    return json.dumps({
        "action": "restart",
        "result": result
    })


@app.route("/server/contextualize", methods=['POST'])
def web_server_contextualize():
    contextualization_data = json.loads(flask.request.data)
    result = server_actions.server_contextualize(contextualization_data)
    return json.dumps(result)


@app.route("/server/update")
def web_server_update():
    result = server_actions.server_update()
    return json.dumps(result)


@app.route("/server/tasks")
def web_server_tasks():
    result = server_actions.server_tasks()
    return json.dumps(result)
