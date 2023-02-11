import unittest

from common import *

# noinspection PyUnresolvedReferences
import jmcomic
from jmcomic import *


class JmTestConfigurable(unittest.TestCase):
    option: JmOption = None
    client: JmcomicClient = None
    application_workspace = "D:/GitProject/dev/pip/crawler-jmcomic/assets/"
    no_proxy_yml = '/config/jmcomic_config_no_proxy.yml'
    use_proxy_yml = '/config/jmcomic_config_use_proxy.yml'

    @classmethod
    def setUpClass(cls, profile=no_proxy_yml):
        set_application_workspace(cls.application_workspace)
        WorkEntity.jm_save_base_dir = workspace("/download/", is_dir=True)
        option_file = workspace(profile)
        option: JmOption = JmOption.create_from_file(option_file)
        # option.save_to_file(option_file)

        cls.option = option
        cls.client = option.build_jm_client()

        cls.try_update_jm_cookies()

    def setUp(self) -> None:
        print(''.center(80, '-'))

    @staticmethod
    def set_workspace_to_resources_dir():
        set_application_workspace(workspace("/resources/", is_dir=True))

    @classmethod
    def try_update_jm_cookies(cls):
        # 尝试更新 cookies
        cookies = ChromePluginCookieParser({'remember', 'comic'}).apply(when_valid_message="更新jmcomic-option成功！！！！")
        if cookies is not None:
            cls.option.request_meta_data['cookies'] = cookies
            cls.option.save_to_file()

    @classmethod
    def use_proxy_yaml_option_and_client(cls):
        cls.setUpClass(profile=cls.use_proxy_yml)
