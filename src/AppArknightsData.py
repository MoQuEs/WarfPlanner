from App.ArknightsData import arknights_data_generator
from App.Init import config, arknights


def main() -> None:
    arknights_data_generator(config, arknights, True)


if __name__ == "__main__":
    main()
