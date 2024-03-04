import typing
from os import cpu_count
from threading import Thread

from waitress import serve
from webview import start as webview_start, create_window

from App.Init import app, listen_addr, listen_port, link, language, config
from App.Routes import main_routes_blueprint


def main() -> None:
    def flask_server() -> typing.Callable:
        return lambda: app.run(
            host=listen_addr,
            port=listen_port,
            debug=config.environment() == "development",
            use_reloader=False,
        )

    def waitress_server() -> typing.Callable:
        cpu = cpu_count()
        if cpu is None:
            cpu = 1

        return lambda: serve(
            app, host=listen_addr, port=listen_port, threads=cpu * 2, _quiet=config.environment() != "development"
        )

    app.register_blueprint(main_routes_blueprint)

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


if __name__ == "__main__":
    main()
