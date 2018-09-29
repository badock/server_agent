import mcrcon

SERVER_IP = "127.0.0.1"
ADMIN_PORT = 25575
RCON_PASSWORD = "adminVYcm1Zfz"


def rcon(command):
    rcon = mcrcon.MCRcon(SERVER_IP, RCON_PASSWORD, ADMIN_PORT)
    rcon.connect()

    result = rcon.command(command)
    rcon.disconnect()

    return result


if __name__ == "__main__":
    prefix, players_str = rcon("list").split(" players online: ")
    players = players_str.split(", ")
    print(players)
