from .app import Application
from .config import AppConfig
from .logging_config import configure_logging


def main() -> None:
    config = AppConfig.from_args()
    configure_logging(config.log_level)
    Application(config).run()


if __name__ == "__main__":
    main()
