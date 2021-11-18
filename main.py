def main():
    from PyQt5.QtWidgets import QApplication
    from gui import App
    from os import mkdir, getcwd, path

    import logging
    import logging.config

    if not path.exists(path.join(getcwd(), 'logs')):
        mkdir(path.join(getcwd(), 'logs'))

    if not path.exists(path.join(getcwd(), 'Novels')):
        mkdir(path.join(getcwd(), 'Novels'))

    logging.basicConfig()
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    root = QApplication([])
    app = App()
    app.show()

#    handler = app.log
#    rootLogger.addHandler(handler)

    exit(root.exec_())


if __name__ == "__main__":
    main()
