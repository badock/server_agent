import logging
from agent.linuxgsm.server_agent import SteamAgentActions

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


class CsgoAgentActions(SteamAgentActions):

    def __init__(self):
        super(CsgoAgentActions, self).__init__()
