import threading
from agent.base import app
from agent.base import logger
from agent.base import DEBUG
from agent.base import update_server_info


threading.Thread(target=update_server_info).start()

if __name__ == "__main__":
    # Run web application
    logger.info("Creating the 'server_agent' web application")
    app.jinja_env.auto_reload = DEBUG

    app.run(host="0.0.0.0", port=5000, debug=DEBUG, threaded=True)
