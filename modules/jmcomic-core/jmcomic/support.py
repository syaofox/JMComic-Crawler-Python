from re import compile, Pattern
from typing import Union

from PIL import Image
from requests import Response
from common import require_not_empty

from .jm_entity import *


class JmModuleConfig:
    HTTPS = "https://"
    DOMAIN = "jmcomic1.rocks"  # jmcomic默认域名
    JM_REDIRECT_URL = 'https://jm365.me/3YeBdF'
    JM_PUB_URL = 'https://jmcomic1.bet'
    JM_SERVER_ERROR_HTML = "Could not connect to mysql! Please check your database settings!"
    JM_CDN_IMAGE_URL_TEMPLATE = 'https://cdn-msp.{domain}/media/photos/{photo_id}/{index:05}{suffix}'  # index 从1开始
    SCRAMBLE_0 = 220980
    SCRAMBLE_10 = 268850
    SCRAMBLE_8 = 421926  # 2023-02-08后改了图片切割算法

    Resp = Response
    enable_jm_debug = True
    debug_printer = print
    retry_image_suffix = ['.jpg', '.webp', '.gif', '.png']
    jm_client_caches = {}

    @classmethod
    def default_headers(cls):
        return {
            'authority': cls.DOMAIN,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
                      'application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'zh-CN,zh;q=0.9',
            'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 '
                          'Safari/537.36',
        }

    # noinspection PyUnusedLocal
    @classmethod
    def jm_debug(cls, topic: str, *args, sep='', end='\n', file=None, from_class='api'):
        if cls.enable_jm_debug is True:
            cls.debug_printer(f'【{topic}】', *args, sep=sep, end=end, file=file)

    @classmethod
    def disable_jm_debug(cls):
        cls.enable_jm_debug = False


jm_debug = JmModuleConfig.jm_debug
disable_jm_debug = JmModuleConfig.disable_jm_debug


class JmcomicText:
    pattern_jm_domain = compile('https://([\w.]+)')
    pattern_jm_pa_id = compile('/(photos?|album)/(\d+)')

    pattern_html_photo_photo_id = compile('<meta property="og:url" content=".*?/(\d+)/?.*?">')
    pattern_html_photo_scramble_id = compile('var scramble_id = (\d+);')
    pattern_html_photo_title = compile('<title>(.*?)\|.*</title>')
    pattern_html_photo_data_original_list = compile('data-original="(.*?)" id="album_photo_.+?"')
    pattern_html_photo_keywords = compile('<meta name="keywords" content="(.*?)" />')
    pattern_html_photo_series_id = compile('var series_id = (\d+);')

    pattern_html_album_album_id = compile('<meta property="og:url" content=".*?/(\d+)/?.*?">')
    pattern_html_album_scramble_id = compile('var scramble_id = (\d+);')
    pattern_html_album_title = compile('panel-heading[\s\S]*?<h1>(.*?)</h1>')
    pattern_html_album_episode_list = compile('<a href=".*?" data-album="(\d+)">\n'
                                              '<li.*>\n第(\d+)話\n(.*)\n'
                                              '<[\s\S]*?>(\d+-\d+-\d+).*?')
    pattern_html_album_page_count = compile('<span class="pagecount">页数:(\d+)</span>')
    pattern_html_album_pub_date = compile('itemprop="datePublished" content=".*?">更新日期 : (.*?)</span>')

    # album 作者
    pattern_html_album_author_list = [
        compile('作者： <span itemprop="author" data-type="author">(\s*<a.*?>(.*?)</a>)*\s*</span>'),
        compile("<a.*?>(.*?)</a>"),
    ]

    @classmethod
    def parse_to_jm_domain(cls, text: str):
        require_not_empty(text)

        if text.startswith("https"):
            return cls.pattern_jm_domain.search(text)[1]

        return text

    @classmethod
    def parse_to_photo_id(cls, text) -> str:
        require_not_empty(text)

        if text is None:
            raise AssertionError('text不能为None')

        if isinstance(text, int):
            return str(text)

        if not isinstance(text, str):
            raise AssertionError(f"无法解析jm车号, 参数类型为: {type(text)}")

        if len(text) <= 2:
            raise AssertionError(f"无法解析jm车号, 文本为: {text}")

        # text: JM12341
        c0 = text[0]
        c1 = text[1]
        if (c0 == 'J' or c0 == 'j') and (c1 == 'M' or c1 == 'm'):
            # JM123456
            return text[2:]

        elif text.isdigit():
            # 123456
            return str(text)

        else:
            # https://xxx/photo/412038
            match = cls.pattern_jm_pa_id.search(text)
            if match is None:
                raise AssertionError(f"无法解析jm车号, 文本为: {text}")
            return match[2]

    @classmethod
    def parse_to_album_id(cls, text) -> str:
        return cls.parse_to_photo_id(text)

    @classmethod
    def analyse_jm_photo_html(cls, html: str) -> JmPhotoDetail:
        require_not_empty(html)

        return cls.reflect_new_instance(
            html,
            "pattern_html_photo_",
            JmPhotoDetail
        )

    @classmethod
    def analyse_jm_album_html(cls, html: str) -> JmAlbumDetail:
        require_not_empty(html)

        return cls.reflect_new_instance(
            html,
            "pattern_html_album_",
            JmAlbumDetail
        )

    @classmethod
    def reflect_new_instance(cls, html: str, cls_field_prefix: str, clazz: type):

        def match_field(field_key: str, pattern: Union[Pattern, List[Pattern]], text):

            if isinstance(pattern, list):
                # 如果是 pattern 是 List[re.Pattern]，
                # 取最后一个 pattern 用于 match field，
                # 其他的 pattern 用来给文本缩小范围（相当于多次正则匹配）
                last_pattern = pattern[len(pattern) - 1]
                # 缩小文本
                for i in range(0, len(pattern) - 1):
                    match = pattern[i].search(text)
                    if match is None:
                        return None
                    text = match[0]
                pattern = last_pattern

            if field_key.endswith("_list"):
                return pattern.findall(text)
            else:
                return pattern.search(text)[1]

        field_dict = {}
        pattern_name: str

        for pattern_name, pattern_value in cls.__dict__.items():
            if not pattern_name.startswith(cls_field_prefix):
                continue

            # 获取字段名和值
            field_name = pattern_name[pattern_name.index(cls_field_prefix) + len(cls_field_prefix):]
            field_value = match_field(field_name, pattern_value, html)

            if field_value is None:
                raise AssertionError(f"文本没有匹配上字段：字段名为{field_name}，pattern为cls.{pattern_name}")

            # 保存字段
            field_dict[field_name] = field_value

        return clazz(**field_dict)


class JmSearchPattern:
    # 用来缩减html的长度
    pattern_html_search_shorten_for = compile('<div class="well well-sm">([\s\S]*)'
                                              '<div class="row">[\s\S]*'
                                              '<div class="bot-per visible-xs visible-sm">')

    # 用来提取搜索页面的的album的信息
    pattern_html_search_album_info_list = compile(
        '<a href="/album/(\d+)/.+"[\s\S]*?'
        'title="(.*?)"[\s\S]*?'
        '(<div class="label-category" style="">'
        '\n(.*)\n</div>\n<div class="label-sub" style=" ">'
        '(.*?)\n<[\s\S]*?)?'
        '<div class="title-truncate tags .*>\n'
        '(<a[\s\S]*?) </div>'
    )

    # 用来查找tag列表
    pattern_html_search_tag_list = compile('<a href=".*?">(.*?)</a>')

    @classmethod
    def analyse_jm_search_html(cls, html: str) -> JmSearchPage:
        html = cls.pattern_html_search_shorten_for.search(html)[0]
        album_info_list = cls.pattern_html_search_album_info_list.findall(html)

        for i, (album_id, title, *args) in enumerate(album_info_list):
            _, category_none, label_sub_none, tag_text = args
            tag_list = cls.pattern_html_search_tag_list.findall(tag_text)
            album_info_list[i] = (album_id, title, category_none, label_sub_none, tag_list)

        return JmSearchPage(album_info_list)


class JmImageSupport:

    @classmethod
    def save_resp_img(cls, resp: JmModuleConfig.Resp, filepath: str):
        cls.open_Image(resp.content).save(filepath)

    @classmethod
    def save_resp_decode_img(cls,
                             resp: JmModuleConfig.Resp,
                             img_detail: JmImageDetail,
                             filepath: str
                             ) -> None:
        cls.decode_and_save(
            cls.calculate_segmentation_num(img_detail),
            cls.open_Image(resp.content),
            filepath
        )

    @classmethod
    def decode_disk_img(cls,
                        img_detail: JmImageDetail,
                        img_filepath: str,
                        decoded_save_path: str
                        ) -> None:
        cls.decode_and_save(
            cls.calculate_segmentation_num(img_detail),
            cls.open_Image(img_filepath),
            decoded_save_path
        )

    @classmethod
    def decode_and_save(cls,
                        num: int,
                        img_src: Image,
                        decoded_save_path: str
                        ) -> None:
        """
        解密图片并保存
        @param num: 分割数，可以用 cls.calculate_segmentation_num 计算
        @param img_src: 原始图片
        @param decoded_save_path: 解密图片的保存路径
        """

        # 无需解密，直接保存
        if num == 0:
            img_src.save(decoded_save_path)
            return

        import math
        w, h = img_src.size

        # 创建新的解密图片
        img_decode = Image.new("RGB", (w, h))
        remainder = h % num
        copyW = w
        for i in range(num):
            copyH = math.floor(h / num)
            py = copyH * i
            y = h - (copyH * (i + 1)) - remainder

            if i == 0:
                copyH += remainder
            else:
                py += remainder

            img_decode.paste(
                img_src.crop((0, y, copyW, y + copyH)),
                (0, py, copyW, py + copyH)
            )

        # 保存到新的解密文件
        img_decode.save(decoded_save_path)

    @classmethod
    def open_Image(cls, fp: Union[str, bytes]):
        from PIL import Image
        from io import BytesIO
        fp = fp if isinstance(fp, str) else BytesIO(fp)
        return Image.open(fp)

    @classmethod
    def calculate_segmentation_num(cls, detail: JmImageDetail) -> int:
        """
        获得图片分割数
        """
        scramble_id = int(detail.scramble_id)
        aid = int(detail.aid)

        if aid < scramble_id:
            return 0
        elif aid < JmModuleConfig.SCRAMBLE_10:
            return 10
        else:
            import hashlib
            x = 10 if aid < JmModuleConfig.SCRAMBLE_8 else 8
            s = f"{aid}{detail.img_file_name}"  # 拼接
            s = s.encode()
            s = hashlib.md5(s).hexdigest()
            num = ord(s[-1])
            num %= x
            num = num * 2 + 2
            return num
