import logging
import subprocess
from agent.linuxgsm.server_agent import LinuxGSMAgentActions
from core.config.config_loader import find_config
import ConfigParser

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


class MinecraftAgentActions(LinuxGSMAgentActions):

    def __init__(self):
        super(MinecraftAgentActions, self).__init__()
        self.server_cmd_path = "%s/mcserver" % self.server_folder_path

    def players(self):
        logger.info("players")
        from core.minecraft.misc import rcon
        prefix, players_str = rcon("list").split(" players online: ")
        if players_str == "":
            return []
        players = players_str.split(", ")
        result = [{"client_id": p, "client_name": p} for p in players]
        return result

    def kick_player(self, player_id):
        from core.minecraft.misc import rcon
        result = rcon("kick %s" % player_id)
        return result

    def ban_player(self, player_id):
        from core.minecraft.misc import rcon
        result = rcon("ban %s" % player_id)
        return result

    def say(self, msg):
        from core.minecraft.misc import rcon
        rcon("say %s" % msg)
        return True

    def cmd(self, cmd):
        from core.minecraft.misc import rcon
        cmd_result = rcon(cmd).split("\n")
        return cmd_result

    def server_contextualize(self, parameters):
        server_config_location = "/home/csgoserver/serverfiles/server.properties"
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


if __name__ == "__main__":
    actions = MinecraftAgentActions()
    players = actions.players()
    print(players)

