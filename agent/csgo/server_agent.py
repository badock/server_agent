import logging
from agent.linuxgsm.server_agent import SteamAgentActions

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


class CsgoAgentActions(SteamAgentActions):

    def __init__(self):
        super(CsgoAgentActions, self).__init__()

    def players(self):
        logger.info("players")
        from core.rcon.rcon_api import get_server_rcon_details
        from core.data.server_agent import SERVER_AGENT_URL
        server_rcon_details = get_server_rcon_details(server_details=self.get_server_info())
        logging.info(server_rcon_details.get("players").values.get("players"))
	result = [{"client_id": x.values.get("name"), "client_name": x.values.get("name")} for x in server_rcon_details.get("players").values.get("players")]
        return result

    def kick_player(self, player_id):
        from core.data.server_agent import SERVER_AGENT_URL
        from core.rcon.rcon_api import server_kick_player
        result = server_kick_player(player_id, server_details=self.get_server_info())
        return result

    def ban_player(self, player_id):
        from core.data.server_agent import SERVER_AGENT_URL
        from core.rcon.rcon_api import server_ban_player
        result = server_ban_player(player_id, server_details=self.get_server_info())
        return result

    def say(self, msg):
        from core.data.server_agent import SERVER_AGENT_URL
        from core.rcon.rcon_api import send_public_message

        send_public_message(msg, server_details=self.get_server_info())
        return True

    def cmd(self, cmd):
        from core.data.server_agent import SERVER_AGENT_URL
        from core.rcon.rcon_api import send_command
        cmd_result_str = send_command(cmd, server_details=self.get_server_info())["text"]
        cmd_result = cmd_result_str.split("\n")
        return cmd_result


if __name__ == "__main__":
    actions = CsgoAgentActions()
    players = actions.players()
    print(players)

