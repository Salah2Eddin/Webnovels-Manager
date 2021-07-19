from os import mkdir, getcwd, path
if not path.exists(path.join(getcwd(), 'Logs')):
    mkdir(path.join(getcwd(), 'Logs'))


def main():
    from PyQt5.QtWidgets import QApplication
    from gui import App

    import logging
    import logging.config

    logging.basicConfig()
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)

    root = QApplication([])
    app = App()
    app.show()

#    handler = app.log
#    rootLogger.addHandler(handler)

    exit(root.exec_())


if __name__ == "__main__":
    main()
