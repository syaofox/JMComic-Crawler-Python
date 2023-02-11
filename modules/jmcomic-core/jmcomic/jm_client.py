import requests
from common import file_exists, change_file_suffix

from .support import *

Resp = JmModuleConfig.Resp


class JmcomicClient:
    debug_from_class = 'jm-client'

    def __init__(self, **kwargs):
        self.meta_data = kwargs
        self.domain = kwargs.pop('domain', JmModuleConfig.DOMAIN)

    def download_image(self,
                       data_original: str,
                       img_save_path: str,
                       scramble_id: str,
                       photo_id: str = None,
                       decode_image=True,
                       ) -> str:
        # 请求图片
        resp = self.request_get(data_original,
                                is_api=False)

        if self.is_empty_image(resp):
            raise AssertionError(f'接收到的图片数据为空: {resp.url}')

        # 不解密图片，直接返回
        if decode_image is False:
            # 保存图片
            JmImageSupport.save_resp_img(resp, img_save_path)
            return img_save_path
        else:
            JmImageSupport.save_resp_decode_img(
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
        return self.download_image(
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
        resp = self.request_get(f"/album/{album_id}")

        # 用 JmcomicText 解析 html，返回实体类
        return JmcomicText.analyse_jm_album_html(resp.text)

    def get_photo_detail(self, jm_photo_id: str) -> JmPhotoDetail:
        # 参数校验
        photo_id = JmcomicText.parse_to_photo_id(jm_photo_id)

        # 请求
        resp = self.request_get(f"/photo/{photo_id}")

        # 用 JmcomicText 解析 html，返回实体类
        return JmcomicText.analyse_jm_photo_html(resp.text)

    def fill_from_album(self, photo_detail: JmPhotoDetail) -> JmAlbumDetail:
        album_detail = self.get_album_detail(photo_detail.album_id)
        photo_detail.from_album = album_detail
        return album_detail

    def fill_photo_data_original(self, photo_detail: JmPhotoDetail):
        resp = self.request_get(f"/photo/{photo_detail.photo_id}")
        photo_detail.data_original_list = JmcomicText.pattern_html_photo_data_original_list.findall(resp.text)

    # -- search --

    def search_album(self, search_query, main_tag=0):
        params = {
            'main_tag': main_tag,
            'search_query': search_query,
        }

        resp = self.request_get('/search/photos', params=params)

        return JmSearchPattern.analyse_jm_search_html(resp.text)

    # -- 对象方法 --

    def of_api_url(self, api_path):
        return f"{JmModuleConfig.HTTPS}{self.domain}{api_path}"

    def request_get(self, url, is_api=True, require_200=True, **kwargs) -> Resp:
        """
        向禁漫发请求的统一入口
        """

        url = self.of_api_url(url) if is_api is True else url
        kwargs = self._merge_request_kwargs(kwargs)

        resp = requests.get(url, **kwargs)

        if require_200 is True and resp.status_code != 200:
            raise AssertionError(f"请求失败，"
                                 f"响应状态码为{resp.status_code}，"
                                 f"URL=[{resp.url}]，"
                                 +
                                 (f"响应文本=[{resp.text}]" if len(
                                     resp.text) < 50 else f'响应文本过长(len={len(resp.text)})，不打印')
                                 )

        if is_api is True and resp.text.strip() == JmModuleConfig.JM_SERVER_ERROR_HTML:
            raise AssertionError("【JM异常】Could not connect to mysql! Please check your database settings!")

        return resp

    def _merge_request_kwargs(self, kwargs) -> dict:
        """
        把 kwargs 合并到 self.meta_data.copy()
        """
        ret = self.meta_data.copy()
        for k, v in kwargs.items():
            ret[k] = v
        return ret

    # -- 配置方法 --

    def add_meta_data(self, key, value):
        self.meta_data[key] = value
        return self

    def remove_meta_data(self, key):
        if key not in self.meta_data:
            return None

        return self.meta_data.pop(key)

    # -- 类方法 --

    @classmethod
    def is_empty_image(cls, resp: Resp):
        return resp.status_code != 200 or len(resp.content) == 0

    @staticmethod
    def debug(topic: str, *args, sep='', end='\n', file=None, from_class=debug_from_class):
        from .support import jm_debug
        jm_debug(topic, *args, sep=sep, end=end, file=file, from_class=from_class)


class CdnCrawler:

    def __init__(self,
                 option: CdnConfig,
                 client: 'JmcomicClient',
                 ):
        self.option = option
        self.client = client

        self.debug = self.client.debug

    def download_photo_from_cdn_directly(self,
                                         req: CdnRequest,
                                         ):
        # 校验参数
        self.option.check_request_is_valid(req)

        # 基本信息
        photo_id = req.photo_id
        scramble_id = req.scramble_id
        use_cache = self.option.use_cache
        decode_image = self.option.decode_image

        # 获得响应
        def get_resp(index: int) -> Tuple[Optional[Resp], str, str]:
            url = self.option.get_cdn_image_url(photo_id, index)
            suffix = self.option.cdn_image_suffix
            pre_try_save_path = req.save_path_provider(url, suffix, index, decode_image)

            # 判断是否命中缓存（预先尝试）
            if use_cache is True and file_exists(pre_try_save_path):
                # 命中，返回特殊值
                return None, suffix, pre_try_save_path
            else:
                return self.try_get_cdn_image_resp(
                    self.client,
                    url,
                    suffix,
                    photo_id,
                    index,
                )

        # 保存响应
        def save_resp(resp_info: Tuple[Optional[Resp], str, str], index: int):
            resp, suffix, img_url = resp_info

            # 1. 判断是不是特殊值
            if resp_info[0] is None:
                # 是，表示命中缓存，直接返回
                save_path = resp_info[2]
                self.debug('图片下载成功',
                           f'photo-{photo_id}: {index}{suffix}命中磁盘缓存 ({save_path})')
                return

            # 2. 判断是否命中缓存
            save_path = req.save_path_provider(img_url, suffix, index, decode_image)
            if use_cache is True and file_exists(save_path):
                # 命中，直接返回
                self.debug('图片下载成功',
                           f'photo-{photo_id}: {index}{suffix}命中磁盘缓存 ({save_path})')
                return

            # 3. 保存图片
            if decode_image is False:
                JmImageSupport.save_resp_img(resp, save_path)
            else:
                JmImageSupport.save_resp_decode_img(
                    resp,
                    JmImageDetail.of(photo_id, scramble_id, data_original=img_url),
                    save_path,
                )

            # 4. debug 消息
            self.debug('图片下载成功',
                       f'photo-{photo_id}: {index}{suffix}下载完成 ('
                       + ('已解码' if decode_image is True else '未解码') +
                       f') [{img_url}] → [{save_path}]')

        # 调用爬虫策略
        self.option.fetch_strategy(
            req.from_index,
            req.photo_len,
            resp_getter=get_resp,
            resp_consumer=save_resp,
        ).do_fetch()

    # 准备提供给爬虫策略的函数
    @staticmethod
    def try_get_cdn_image_resp(client: JmcomicClient,
                               url: str,
                               suffix: str,
                               photo_id,
                               index,
                               ) -> Optional[Tuple[Resp, str, str]]:
        resp = client.request_get(url, False, False)

        # 第一次校验，不空则直接返回
        if not client.is_empty_image(resp):
            return resp, suffix, url

        # 下面进行重试
        client.debug(
            '图片获取重试',
            f'photo-{photo_id}，图片序号为{index}，url=[{url}]'
        )

        # 重试点1：是否文件后缀名不对？
        for alter_suffix in JmModuleConfig.retry_image_suffix:
            url = change_file_suffix(url, alter_suffix)
            resp = client.request_get(url, False, False)
            if not client.is_empty_image(resp):
                client.debug(
                    '图片获取重试 → 成功√',
                    f'更改请求后缀（{suffix} -> {alter_suffix}），url={url}'
                )
                return resp, alter_suffix, url

        # 结论：可能是图片到头了
        client.debug(
            '图片获取重试 ← 失败×',
            f'更换后缀名不成功，停止爬取。'
            f'(推断本子长度<={index - 1}。当前图片序号为{index}，已经到达尽头，'
            f'photo-{photo_id})'
        )
