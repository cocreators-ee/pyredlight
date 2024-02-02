from os import system
from pathlib import Path

import uvicorn
from uvicorn.supervisors import ChangeReload


def main():
    system("poetry install")  # nosec

    reload_dirs = [str(Path(__file__).parent.absolute())]
    config = uvicorn.Config(
        log_level="debug",
        reload=True,
        reload_dirs=reload_dirs,
        app="example_app.main:app",
    )
    server = uvicorn.Server(config)

    supervisor = ChangeReload(config, target=server.run, sockets=[config.bind_socket()])
    supervisor.run()


if __name__ == "__main__":
    main()
