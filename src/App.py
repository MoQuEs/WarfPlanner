from os import cpu_count
from threading import Thread

from waitress import serve
from webview import start as webview_start, create_window

from Init import app, listen_addr, listen_port, link, language, config
from Routes import main


def flask_server() -> callable:
    return lambda: app.run(
        host=listen_addr,
        port=listen_port,
        debug=config.environment() == "development",
        use_reloader=False,
    )


def waitress_server() -> callable:
    return lambda: serve(
        app, host=listen_addr, port=listen_port, threads=cpu_count() * 2, _quiet=config.environment() != "development"
    )


app.register_blueprint(main)

try:
    if config.environment() == "flask":
        target = flask_server()
    else:
        target = waitress_server()

    if config.mode() == "browser":
        print("Link: %s" % link)
        target()

    else:
        server_thread = Thread(target=target)
        server_thread.daemon = True
        server_thread.start()

        win = create_window(
            title=language.get_text("title"),
            url=link,
        )
        webview_start()
except Exception as ex:
    print(ex)
finally:
    exit()
