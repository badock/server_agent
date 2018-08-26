import logging
import subprocess
import time
import re
import uuid
from core.config.config_loader import find_config
import ConfigParser
from agent.agent_actions import AgentActions

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


def remove_ansi_char(text):
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)


class SteamAgentActions(AgentActions):

    def __init__(self):
        self.server_folder_path = "/home/csgoserver"
        self.server_cmd_path = "%s/csgoserver" % self.server_folder_path
        self.tasks = {}
        self.server_info = None

    def fetch_server_info(self):
        return {
            "server": {
                "server_name": "ottd",
                "password": "unknown",
                "rcon_password": "unknown"
            },
            "updated_server_status": "UKNOWN",

        }

    def get_server_info(self):
        if self.server_info is None:
            self.server_info = self.fetch_server_info()
        return self.server_info

    def get_console_log(self, num_page):
        console_log_path = "/tmp/ottd.log"
        logger.info("console_log_path: %s" % console_log_path)
        cmd = """cat %s """ % (console_log_path)

        proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
        stdout = proc.communicate(cmd)
        lines = stdout[0].split("\n")

        return {
            "status": "OK",
            "logfile": console_log_path,
            "content": lines
        }

    def get_task_log(self, task_id):
        if task_id not in self.tasks:
            return {
                "output": []
            }

        task = self.tasks.get(task_id)

        f = open(task.get("log_file"), "r")
        lines = [remove_ansi_char(line) for line in f.readlines()]

        return {
            "output": lines
        }

    def server_start(self):
        task_uuid = str(uuid.uuid4())
        tmp_log_file = "/tmp/%s.log" % (task_uuid)

        cmd = '/usr/games/openttd -f -D > /tmp/ottd.log 2>&1; echo "dedicated server started" > %s ' % (self.server_cmd_path, tmp_log_file)
        proc = subprocess.Popen(['/bin/bash', '-c', cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)

        self.tasks[task_uuid] = {
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

    def server_stop(self):
        task_uuid = str(uuid.uuid4())
        tmp_log_file = "/tmp/%s.log" % (task_uuid)

        cmd = 'pkill -9 openttd > %s 2>&1' % (tmp_log_file)
        proc = subprocess.Popen(['/bin/bash', '-c', cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)

        self.tasks[task_uuid] = {
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

    def server_restart(self):
        logger.warn("WARNING: restart is not yet supported by ottd :-(")

        return {
            "started": False,
            "task_id": None,
            "action_type": "restart",
            "log_file": None
        }

    def server_update(self):
        logger.warn("WARNING: update is not yet supported by ottd :-(")

        return {
            "started": False,
            "task_id": None,
            "action_type": "update",
            "log_file": None
        }

    def server_contextualize(self, parameters):
        logger.warn("WARNING: Contextualization is not yet supported by ottd :-(")

        return {
            "msg": "OK"
        }

    def server_tasks(self):
        result = {}
        for task_id, task in self.tasks.iteritems():
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
