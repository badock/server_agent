import flask
import flask_login
from flask import Flask
from flask import render_template
from datetime import datetime
import requests

login_manager = flask_login.LoginManager()
# SERVER_AGENT_URL = "http://127.0.0.1:5000"

DEBUG = True
app = Flask(__name__)
app.secret_key = "GamingFogKey1"
# USE_SESSION_FOR_NEXT = True
login_manager.init_app(app)

login_manager.login_view = "login"


@app.template_filter()
def timesince(dt, default="just now"):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    """

    now = datetime.utcnow()

    diff = now - dt

    periods = (
        (diff.days / 365, "year", "years"),
        (diff.days / 30, "month", "months"),
        (diff.days / 7, "week", "weeks"),
        (diff.days, "day", "days"),
        (diff.seconds / 3600, "hour", "hours"),
        (diff.seconds / 60, "minute", "minutes"),
        (diff.seconds, "second", "seconds"),
    )

    for period, singular, plural in periods:
        if period:
            return "%d %s ago" % (period, singular if period == 1 else plural)

    return default


@app.template_filter()
def prettify_duration(dt, default="just now"):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    """

    diff = dt

    nb_seconds = diff % 60
    nb_minutes = (diff - nb_seconds) / 60
    nb_hours = (diff - nb_seconds - nb_minutes * 60) / 3600

    periods = (
        (nb_hours, "hour", "hours"),
        (nb_minutes, "minute", "minutes"),
        (nb_seconds, "second", "seconds"),
    )

    result = []

    for period, singular, plural in periods:
        # if period:
        result += ["%d %s" % (period, singular if period == 1 else plural)]

    return ", ".join(result)


@login_manager.user_loader
def user_loader(email):
    from login_management import users, User
    if email not in users:
        return

    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    from login_management import users, User
    email = request.form.get('email')
    if email not in users:
        return

    user = User()
    user.id = email

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    user.is_authenticated = request.form['password'] == users[email]['password']

    return user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        next_url = flask.request.args.get("next")
        return render_template("login.html", next_url=next_url)
    from login_management import User, authenticate
    email = flask.request.form['email']
    password = flask.request.form['password']
    next_url = flask.request.form['next_url']
    if authenticate(email, password):
        user = User()
        user.id = email
        flask_login.login_user(user)
        redirect_url = next_url if (next_url is not None and next_url != "None") else "home"
        return flask.redirect(redirect_url)

    return 'Bad login'


@app.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("home"))


@app.route("/")
@app.route("/home")
@app.route("/overview")
def overview():
    from core.data.server_agent import SERVER_AGENT_URL
    from core.rcon.rcon_api import get_server_details, get_server_rcon_details, get_server_status, get_server_public_url
    server_details = get_server_details(SERVER_AGENT_URL)
    server_rcon_details = get_server_rcon_details(SERVER_AGENT_URL)
    updated_server_status = get_server_status(SERVER_AGENT_URL)
    public_url = get_server_public_url()

    return render_template("overview.html",
                           server_details=server_details,
                           server_rcon_details=server_rcon_details,
                           updated_server_status=updated_server_status,
                           public_url=public_url)


@app.route("/actions?action=<action>")
@app.route("/actions?cmd_result=<cmd_result>")
@app.route("/actions")
def actions(action=None, cmd_result=None):
    from core.data.server_agent import SERVER_AGENT_URL
    if action in ["start", "restart", "stop", "update"]:
        if action == "start":
            from core.rcon.rcon_api import start_server
            start_server(SERVER_AGENT_URL)
        elif action == "restart":
            from core.rcon.rcon_api import restart_server
            restart_server(SERVER_AGENT_URL)
        elif action == "stop":
            from core.rcon.rcon_api import stop_server
            stop_server(SERVER_AGENT_URL)
        elif action == "update":
            from core.rcon.rcon_api import update_server
            update_server(SERVER_AGENT_URL)
        return flask.redirect(flask.url_for("actions"))

    from core.rcon.rcon_api import get_server_details, get_server_rcon_details, get_server_tasks
    server_details = get_server_details(SERVER_AGENT_URL)
    server_rcon_details = get_server_rcon_details(SERVER_AGENT_URL)
    server_tasks = get_server_tasks(SERVER_AGENT_URL)

    for server_task_id, server_task in server_tasks.iteritems():
        server_task["datetime"] = datetime.utcfromtimestamp(server_task.get("created_at"))

    return render_template("actions.html",
                           # server=server,
                           server_details=server_details,
                           server_rcon_details=server_rcon_details,
                           server_tasks=server_tasks,
                           cmd_result=cmd_result)


@app.route("/task/<task_id>/logs")
def task_logs(task_id):
    from core.data.server_agent import SERVER_AGENT_URL
    from core.rcon.rcon_api import get_server_tasks, get_server_task_output, get_server_details
    server_details = get_server_details(SERVER_AGENT_URL)
    server_tasks = get_server_tasks(SERVER_AGENT_URL)
    server_task_output = get_server_task_output(SERVER_AGENT_URL, task_id)

    return render_template("task_logs.html",
                           server_tasks=server_tasks,
                           server_details=server_details,
                           server_task_output=server_task_output)


@app.route("/players")
def players():
    from core.data.server_agent import SERVER_AGENT_URL

    players = requests.get("%s/server/players" % SERVER_AGENT_URL).json()

    return render_template("players.html",
                           players=players)


@app.route("/logs/num_page=<int:num_page>")
@app.route("/logs")
def logs(num_page=1):
    from core.data.server_agent import SERVER_AGENT_URL
    from core.rcon.rcon_api import get_server_details, get_server_rcon_details, get_server_console
    server_details = get_server_details(SERVER_AGENT_URL)
    server_rcon_details = get_server_rcon_details(SERVER_AGENT_URL)
    server_console = get_server_console(SERVER_AGENT_URL, num_page)

    return render_template("logs.html",
                           # server=server,
                           server_details=server_details,
                           server_rcon_details=server_rcon_details,
                           server_console=server_console)


@app.route("/msg", methods=["POST"])
def send_message():
    from core.data.server_agent import SERVER_AGENT_URL

    if "msg" in flask.request.form:
        msg = flask.request.form.get("msg")

        post_data = {
            "msg": msg
        }
        requests.post("%s/server/say" % SERVER_AGENT_URL, post_data)

    return flask.redirect(flask.url_for("actions"))


@app.route("/cmd", methods=["POST"])
def send_command():
    from core.data.server_agent import SERVER_AGENT_URL

    cmd_result = []
    if "cmd" in flask.request.form:
        cmd = flask.request.form.get("cmd")

        post_data = {
            "cmd": cmd
        }
        cmd_result = requests.post("%s/server/cmd" % SERVER_AGENT_URL, post_data)

    return actions(cmd_result=cmd_result)


@app.route("/kick/<player>")
def kick_player(player):
    from core.data.server_agent import SERVER_AGENT_URL

    players = requests.get("%s/server/kick/%s" % (SERVER_AGENT_URL, player)).json()

    return flask.redirect(flask.url_for("players"))


@app.route("/ban/<player>")
def ban_player(player):
    from core.data.server_agent import SERVER_AGENT_URL

    players = requests.get("%s/server/kick/%s" % (SERVER_AGENT_URL, player)).json()

    return flask.redirect(flask.url_for("players"))


if __name__ == '__main__':
    # Run web application
    print("Creating web app")
    app.jinja_env.auto_reload = DEBUG
    app.run(host="0.0.0.0", port=5010, debug=DEBUG, threaded=True)
