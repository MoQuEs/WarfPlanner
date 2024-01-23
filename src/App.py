from os import cpu_count
from threading import Thread

from waitress import serve
from webbrowser import open as web_open
from webview import start as webview_start, create_window

from Init import app, listen_addr, listen_port, link, language, config
from Routes import main


def dev_server() -> callable:
    return lambda: app.run(
        host=listen_addr,
        port=listen_port,
        debug=config.environment() == "development",
        use_reloader=False,
    )


def prod_server() -> callable:
    return lambda: serve(
        app, host=listen_addr, port=listen_port, threads=cpu_count(), _quiet=True
    )


app.register_blueprint(main)

try:
    if config.mode() == "browser":
        print("Link: %s" % link)
        if config.environment() == "development":
            dev_server()()
        else:
            web_open(link)
            prod_server()()

    else:
        if config.environment() == "development":
            target = dev_server()
        else:
            target = prod_server()

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
