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


class LinuxGSMAgentActions(AgentActions):

    def __init__(self):
        self.server_folder_path = "/home/csgoserver"
        self.server_cmd_path = "%s/csgoserver" % self.server_folder_path
        self.tasks = {}
        self.server_info = None

    def fetch_server_info(self):
        proc = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
        stdout = proc.communicate('%s details' % self.server_cmd_path)

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

    def get_server_info(self):
        if self.server_info is None:
            self.server_info = self.fetch_server_info()
        return self.server_info

    def get_console_log(self, num_page):
        info = self.get_server_info()
        service_name = info["script"]["service_name"]

        console_log_path = "%s/log/console/%s-console.log" % (self.server_cmd_path, service_name)
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

        cmd = '%s start > %s 2>&1' % (self.server_cmd_path, tmp_log_file)
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

        cmd = '%s stop > %s 2>&1' % (self.server_cmd_path, tmp_log_file)
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
        task_uuid = str(uuid.uuid4())
        tmp_log_file = "/tmp/%s.log" % (task_uuid)

        cmd = '%s restart > %s 2>&1' % (self.server_cmd_path, tmp_log_file)
        proc = subprocess.Popen(['/bin/bash', '-c', cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)

        self.tasks[task_uuid] = {
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

    def server_update(self):
        task_uuid = str(uuid.uuid4())
        tmp_log_file = "/tmp/%s.log" % (task_uuid)

        cmd = '%s update > %s 2>&1' % (self.server_cmd_path, tmp_log_file)
        proc = subprocess.Popen(['/bin/bash', '-c', cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)

        self.tasks[task_uuid] = {
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

    def server_contextualize(self, parameters):
        server_config_location = "/home/csgoserver/lgsm/config-lgsm/csgoserver/csgoserver.cfg"
        cmd = ""
        for (k, v) in parameters.iteritems():
            cmd += 'sed -i "s/%s=.*//g" %s;' % (k, server_config_location)
            cmd += 'echo -e "\n%s=%s" >> %s;' % (k, v, server_config_location)
            cmd += "grep -v '^ *$' %s > tmp && mv tmp %s;" % (server_config_location, server_config_location)
        proc = subprocess.Popen(['/bin/bash', '-c', cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
        # Contextualize config file with public address
        config_file_path = find_config()
        if config_file_path is not None:
            public_url = parameters.get("public_url")
            logger.info("writing public url '%s' in config file" % public_url)

            config = ConfigParser.SafeConfigParser()
            config.read(config_file_path)
            if "server" not in config.sections():
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

    def players(self):
        raise NotImplemented()

    def kick_player(self, player_id):
        raise NotImplemented()
