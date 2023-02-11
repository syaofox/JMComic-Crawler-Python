from common import *

from jmcomic import download_album, option


def main():
    set_application_workspace('D:/GitProject/dev/pip/crawler-jmcomic/assets/config')
    download_album(
        '422866',
        option('jmcomic_config_no_proxy.yml'),
    )


if __name__ == '__main__':
    main()
