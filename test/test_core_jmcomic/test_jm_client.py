from test_core_jmcomic import *


class Test_Client(JmTestConfigurable):

    def setUp(self):
        set_global_proxy('off')

    def test_use_proxy(self):
        # set_global_proxy('on')
        # self.use_proxy_yaml_option_and_client()
        # print(self.client.get_album_detail('385360'))
        # url = "https://cdn-msp.jmcomic1.rocks/media/photos/392497/00001.webp"
        # resp = self.client._request_get(
        #     url,
        #     is_api=False,
        #     proxies=ProxyBuilder.clash_proxy()
        # )
        # print(resp.status_code)
        # print(len(resp.content))
        pass

    def test_download_from_cdn_directly(self):
        photo_id = 'JM15193'
        option = self.option
        cdn_crawler = option.build_cdn_crawler()
        cdn_crawler.download_photo_from_cdn_directly(
            option.build_cdn_request(photo_id),
        )

    def test_download_image(self):
        jm_photo_id = 'JM15193'
        photo_detail = self.client.get_photo_detail(jm_photo_id)
        self.client.download_by_image_detail(
            photo_detail[0],
            img_save_path=workspace("./test_download_image.png")
        )

    def test_get_album_detail_by_jm_photo_id(self):
        album_id = "JM15193"
        print_obj_dict(self.client.get_album_detail(album_id))

    def test_get_photo_detail_by_jm_photo_id(self):
        """
        测试通过 JmcomicClient 和 jm_photo_id 获取 JmPhotoDetail对象
        """
        jm_photo_id = 'JM15193'
        photo_detail = self.client.get_photo_detail(jm_photo_id)
        photo_detail.when_del_save_file = True
        photo_detail.after_save_print_info = True
        del photo_detail

    def test_multi_album_and_single_album(self):
        multi_photo_album_id = [
            "195822",
        ]

        for album_id in multi_photo_album_id:
            album_detail: JmAlbumDetail = self.client.get_album_detail(album_id)
            print(f'本子: [{album_detail.title}] 一共有{album_detail.page_count}页图')

    def test_search(self):
        jm_search_page = self.client.search_album('MANA')
        for album_id in jm_search_page.album_id_iter():
            print(album_id)
