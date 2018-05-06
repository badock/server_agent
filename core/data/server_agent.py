from core.config.config_loader import load_config

SERVER_AGENT_URL = load_config().get("server_agent").get("url")