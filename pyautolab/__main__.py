from multiprocessing import freeze_support

from pyautolab.app.app import App
from pyautolab.app.commands import register_default_commands


def main():
    freeze_support()

    app = App()

    register_default_commands()
    app.load_plugins()
    app.window.show()
    app.qt_app.exec()


if __name__ == "__main__":
    main()
