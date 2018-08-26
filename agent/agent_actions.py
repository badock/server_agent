
class AgentActions(object):

    def fetch_server_info(self):
        raise NotImplemented()

    def get_server_info(self):
        raise NotImplemented()

    def get_console_log(self, num_page):
        raise NotImplemented()

    def get_task_log(self, task_id):
        raise NotImplemented()

    def server_start(self):
        raise NotImplemented()

    def server_stop(self):
        raise NotImplemented()

    def server_restart(self):
        raise NotImplemented()

    def server_update(self):
        raise NotImplemented()

    def server_contextualize(self, parameters):
        raise NotImplemented()

    def server_tasks(self):
        raise NotImplemented()


def instantiate_agent_actions(game_name):
    if game_name == "csgo":
        from csgo.server_agent import CsgoAgentActions
        return CsgoAgentActions()
    elif game_name == "ottd":
        from ottd.server_agent import OttdAgentActions
        return OttdAgentActions()
    raise Exception("Could not import the agent actions for game '%s'" % game_name)
