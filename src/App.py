import sys
import threading
import webbrowser

import webview
from waitress import serve

from Init import app, listen_addr, listen_port, link, i18t, config
from Routes import main
from Utils import cpu_count


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
            webbrowser.open(link)
            prod_server()()

    else:
        if config.environment() == "development":
            target = dev_server()
        else:
            target = prod_server()

        server_thread = threading.Thread(target=target)
        server_thread.daemon = True
        server_thread.start()

        win = webview.create_window(
            title=i18t("title"),
            url=link,
            # frameless=True,
        )
        webview.start()
except Exception as ex:
    print(ex)
finally:
    sys.exit()
