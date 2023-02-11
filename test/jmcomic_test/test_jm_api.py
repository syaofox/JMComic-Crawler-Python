from jmcomic_test import *


class Test_Api(JmTestConfigurable):

    def test_download_photo_by_id(self):
        """
        测试jmcomic模块的api的使用
        """
        photo_id = "412038"
        jmcomic.download_photo(photo_id, self.option)

    def test_download_album_by_id(self):
        """
        测试jmcomic模块的api的使用
        """
        set_global_proxy()
        # self.client.add_meta_data('verify', False)
        album_id_ls = [
            # '219757',
            '15193',
            # 'JM412038'
        ]

        jmcomic.download_album(album_id_ls[0], self.option)
        # multi_thread_launcher(
        #     iter_objs=album_id_ls,
        #     apply_each_obj_func=lambda album_id: jmcomic.download_album(album_id, self.option),
        #     wait_finish=True
        # )
