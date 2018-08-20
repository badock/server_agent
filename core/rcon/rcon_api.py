import valve.source
import valve.source.a2s
import valve.source.master_server
import valve.rcon
import requests


def dispatch_action_server(server_url, action):
    try:
        r = requests.get("%s/server/%s" % (server_url, action))
        if r.status_code == 200:
            return {"result": "ok"}
        else:
            return {"result": "ko", "error_code": r.status_code}
    except requests.ConnectionError:
            return {"result": "ko", "reason": "ConnectionError"}


def start_server(server_url):
    return dispatch_action_server(server_url, "start")


def restart_server(server_url):
    return dispatch_action_server(server_url, "restart")


def stop_server(server_url):
    return dispatch_action_server(server_url, "stop")


def update_server(server_url):
    return dispatch_action_server(server_url, "update")


def get_server_details(server_url):
    server_details_json_str = requests.get("%s/server/details" % (server_url))
    result = server_details_json_str.json()
    return result


def get_server_tasks(server_url):
    server_tasks_json_str = requests.get("%s/server/tasks" % (server_url))
    result = server_tasks_json_str.json()
    return result


def get_server_task_output(server_url, task_id):
    server_task_output_json_str = requests.get("%s/server/tasks/%s/output" % (server_url, task_id))
    result = server_task_output_json_str.json()
    return result


def get_server_status(server_url):
    server_status_json_str = requests.get("%s/server/status" % (server_url))
    result = server_status_json_str.json()
    return result


def get_server_console(server_url, num_page):
    server_details_json_str = requests.get("%s/server/console/num_page=%s" % (server_url, num_page))
    result = server_details_json_str.json()
    return result


def get_server_rcon_details(server_url):
    server_details = get_server_details(server_url)

    server_url = server_details.get("server", {}).get("server_ip", "127.0.0.1")

    ip, port_str = server_url.split(":")

    ip = "csgo.jonathanpastor.fr"
    address = (ip, int(port_str))

    offline_value = "OFFLINE"
    result = {
        "info": {},
        "players": {}
    }
    if server_details.get("server", offline_value).get("status", offline_value) == "ONLINE":
        try:
            with valve.source.a2s.ServerQuerier(address, timeout=2.0) as server:
                info = server.info()
                players = server.players()

                result = {
                    "info": info,
                    "players": players
                }
        except valve.source.NoResponseError:
            print("Could not fetch RCON values for server '%s:%s'" % (address))

    return result


def send_command(server_url, cmd):
    server_details = get_server_details(server_url)
    server_status = get_server_status(server_url).get("status")

    server_url = server_details.get("server", {}).get("server_ip", "127.0.0.1")

    ip, port_str = server_url.split(":")

    ip = "csgo.jonathanpastor.fr"
    address = (ip, int(port_str))

    offline_value = "OFFLINE"
    result = {
        "info": {},
        "players": {},
        "text": "Failed"
    }
    password = server_details.get("server", {}).get("rcon_password", None)
    if server_status == "ONLINE":
        try:
            with valve.rcon.RCON(address, password) as rcon:
                try:
                    response = rcon.execute(cmd)
                    result["text"] = response.text
                except:
                    result["text"] = "lost connection with server. Map may have changed!"
        except valve.source.NoResponseError:
            print("Could not fetch RCON values for server '%s:%s'" % (address))

    return result


def send_public_message(server_url, msg):
    return send_command(server_url, "say %s" % msg)


def server_kick_player(server_url, player):
    return send_command(server_url, "kick %s" % player)


def server_ban_player(server_url, player):
    return send_command(server_url, "ban %s" % player)
