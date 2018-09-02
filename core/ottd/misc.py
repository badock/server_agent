from libopenttd.query.master import MasterServerSocket
from libopenttd.query.server import send as s_send
import socket
from libottdadmin2.client import AdminClient, AdminRcon, ServerRcon, ServerRconEnd

SERVER_IP = "192.168.0.21"
GAME_PORT = 4979
ADMIN_PORT = 4977
RCON_PASSWORD = "badock"


def get_server_info():
    master_address = tuple([SERVER_IP, GAME_PORT])

    master_socket = MasterServerSocket()

    # Getting information
    master_socket.send_packet(master_address, s_send.ServerInformation())

    master_socket.process_send()
    master_socket.process_recv()

    server_info = {}

    packets = master_socket.process_packets()
    for master_address, packet in packets:
        server_info = packet.__dict__

    master_socket.close()
    return server_info


def get_detailed_server_info():
    master_address = tuple([SERVER_IP, GAME_PORT])

    master_socket = MasterServerSocket()

    master_socket.send_packet(master_address, s_send.DetailInformation())

    master_socket.process_send()
    master_socket.process_recv()

    server_detailed_info = {}

    packets = master_socket.process_packets()
    for master_address, packet in packets:
        server_detailed_info = packet.__dict__

    master_socket.close()
    return server_detailed_info


def rcon(command):
    connection = AdminClient()
    connection.settimeout(0.4)
    connection.configure(password=RCON_PASSWORD, host=SERVER_IP, port=ADMIN_PORT)
    connection.connect()
    failed = False
    try:
        protocol_response = connection.recv_packet()
        welcome_response = connection.recv_packet()
    except socket.error:
        failed = True

    if protocol_response is None or welcome_response is None:
        failed = True

    result = []
    if failed:
        print("Unable to connect to %(host)s:%(port)s" % {'host': options.host, 'port': options.port})
    else:
        connection.send_packet(AdminRcon, command=command)

        cont = True
        while cont:
            packets = connection.poll()
            if packets is None or packets is False:
                print("Connection lost!")
                break
            cont = len(packets) > 0
            for packet, data in packets:
                if packet == ServerRcon:
                    print(">>> %s" % data['result'])
                    result += data['result']
                elif packet == ServerRconEnd:
                    print("<<< END OF COMMAND >>>")
                    cont = False
                    break
                else:
                    pass
    connection.disconnect()

    return result


if __name__ == "__main__":
    print(get_server_info())
    print(get_detailed_server_info())
    print(rcon("clients"))
