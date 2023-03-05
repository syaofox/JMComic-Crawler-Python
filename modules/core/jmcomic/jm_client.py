from .jm_toolkit import *


class JmcomicClient(PostmanProxy):
    debug_from_class = 'jm-client'

    def __init__(self, postman: Postman, domain):
        super().__init__(postman)
        self.domain = domain

    def download_image(self,
                       data_original: str,
                       img_save_path: str,
                       scramble_id: str,
                       photo_id: str = None,
                       decode_image=True,
                       ):
        """
        下载JM的图片
        @param data_original: 图片url
        @param img_save_path: 图片保存位置
        @param scramble_id: 图片所在photo的scramble_id
        @param photo_id: 图片所在photo的photo_id，可为空
        @param decode_image: 要保存的是解密后的图还是原图
        """
        # 请求图片
        resp = self.jm_get(data_original, is_api=False)

        if self.is_empty_image(resp):
            raise AssertionError(f'接收到的图片数据为空: {resp.url}')

        # gif图无需加解密，需要最先判断
        if self.img_is_not_need_to_decode(data_original, resp):
            JmImageSupport.save_resp_img(resp, img_save_path, False)
            return

        # 不解密图片，直接返回
        if decode_image is False:
            # 保存图片
            JmImageSupport.save_resp_img(
                resp,
                img_save_path,
                need_convert=suffix_not_equal(data_original, img_save_path),
            )

        JmImageSupport.save_resp_decoded_img(
            resp=resp,
            img_detail=JmImageDetail.of(
                photo_id or JmcomicText.parse_to_photo_id(data_original),
                scramble_id,
                data_original,
            ),
            filepath=img_save_path
        )

    def download_by_image_detail(self,
                                 img_detail: JmImageDetail,
                                 img_save_path,
                                 decode_image=True,
                                 ):
        self.download_image(
            img_detail.img_url,
            img_save_path,
            img_detail.scramble_id,
            photo_id=img_detail.aid,
            decode_image=decode_image,
        )

    # -- get detail（返回值是实体类） --

    def get_album_detail(self, album_id) -> JmAlbumDetail:
        # 参数校验
        album_id = JmcomicText.parse_to_photo_id(album_id)

        # 请求
        resp = self.jm_get(f"/album/{album_id}")

        # 用 JmcomicText 解析 html，返回实体类
        return JmcomicText.analyse_jm_album_html(resp.text)

    def get_photo_detail(self, jm_photo_id: str) -> JmPhotoDetail:
        # 参数校验
        photo_id = JmcomicText.parse_to_photo_id(jm_photo_id)

        # 请求
        resp = self.jm_get(f"/photo/{photo_id}")

        # 用 JmcomicText 解析 html，返回实体类
        return JmcomicText.analyse_jm_photo_html(resp.text)

    def fill_from_album(self, photo_detail: JmPhotoDetail) -> JmAlbumDetail:
        """
        获取 photo_detail 所在的 album。
        并把 album_detail 赋值给 photo_detail.from_album
        """
        album_detail = self.get_album_detail(photo_detail.album_id)
        photo_detail.from_album = album_detail
        return album_detail

    def fill_photo_data_original(self, photo_detail: JmPhotoDetail):
        """
        为 photo_detail.data_original_list 赋值
        """
        resp = self.jm_get(f"/photo/{photo_detail.photo_id}")
        photo_detail.data_original_list = JmcomicText.pattern_html_photo_data_original_list.findall(resp.text)

    # -- search --

    def search_album(self, search_query, main_tag=0) -> JmSearchPage:
        params = {
            'main_tag': main_tag,
            'search_query': search_query,
        }

        resp = self.jm_get('/search/photos', params=params)

        return JmSearchSupport.analyse_jm_search_html(resp.text)

    # -- 对象方法 --

    def of_api_url(self, api_path):
        return f"{JmModuleConfig.HTTP}{self.domain}{api_path}"

    def jm_get(self, url, is_api=True, require_200=True, **kwargs) -> ReqResp:
        """
        向禁漫发请求的统一入口
        """
        url = self.of_api_url(url) if is_api is True else url
        if is_api is True:
            self.debug("api", url)

        resp = self.get(url, **kwargs)

        if require_200 is True and resp.status_code != 200:
            write_text('./resp.html', resp.text)
            raise AssertionError(f"请求失败，"
                                 f"响应状态码为{resp.status_code}，"
                                 f"URL=[{resp.url}]，"
                                 +
                                 (f"响应文本=[{resp.text}]" if len(resp.text) < 50 else
                                  f'响应文本过长(len={len(resp.text)})，不打印')
                                 )

        if is_api is True and resp.text.strip() == JmModuleConfig.JM_SERVER_ERROR_HTML:
            raise AssertionError("【JM异常】Could not connect to mysql! Please check your database settings!")

        return resp

    # -- 类方法 --

    @classmethod
    def is_empty_image(cls, resp: ReqResp):
        return resp.status_code != 200 or len(resp.content) == 0

    @staticmethod
    def debug(topic: str, *args, sep='', end='\n', file=None, from_class=debug_from_class):
        jm_debug(topic, *args, sep=sep, end=end, file=file, from_class=from_class)

    @classmethod
    def img_is_not_need_to_decode(cls, data_original: str, _resp: ReqResp):
        return data_original.endswith('.gif')


# 爬取策略
class FetchStrategy:

    def __init__(self,
                 from_index,
                 photo_len,
                 resp_getter,
                 resp_consumer,
                 ):
        self.from_index = from_index
        self.photo_len = photo_len
        self.resp_getter = resp_getter
        self.resp_consumer = resp_consumer

    def do_fetch(self):
        raise NotImplementedError

    def args(self):
        return (self.from_index,
                self.photo_len,
                self.resp_getter,
                self.resp_consumer,
                )
