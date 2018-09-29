import mcrcon

SERVER_IP = "172.17.0.2"
ADMIN_PORT = 25575
RCON_PASSWORD = "adminVYcm1Zfz"
MINECRAFT_CONFIG_LOCATION = "/home/csgoserver/serverfiles/server.properties"


def rcon(command, server_details):
    server_ip, port = server_details.get("server", {}).get("server_ip", "127.0.0.1:25575").split(":")
    password = server_details.get("server", {}).get("rcon_password", None)
    rcon = mcrcon.MCRcon(server_ip, password, ADMIN_PORT)
    rcon.connect()

    result = rcon.command(command)
    rcon.disconnect()

    return result


if __name__ == "__main__":
    prefix, players_str = rcon("list", {"server": {"server_ip": "172.17.0.2:25565", "rcon_password": "XXXX"}}).split(" players online: ")
    players = players_str.split(", ")
    print(players)
