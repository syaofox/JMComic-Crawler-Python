from .jm_service import *


# 目录树的组成
class DownloadDirTree:
    # 根目录 / Album作者 / Photo标题 / 图片文件
    Bd_Author_Title_Image = 0
    # 根目录 / Album作者 / Photo号 / 图片文件
    Bd_Author_Id_Image = 1

    # 根目录 / Album标题 / Photo标题 / 图片文件
    Bd_Title_Title_Image = 2
    # 根目录 / Album标题 / Photo号 / 图片文件
    Bd_Title_Id_Image = 3

    # 根目录 / Photo标题 / 图片文件
    Bd_Title_Image = 4
    # 根目录 / Photo号 / 图片文件
    Bd_Id_Image = 5

    AdditionalHandler = Callable[[Optional[JmAlbumDetail], Optional[JmPhotoDetail]], str]
    additional_tree_flag_handler_mapping: Dict[int, AdditionalHandler] = {}

    def __init__(self,
                 Bd: str,
                 flag: Union[str, int],
                 ):
        self.Bd = fix_filepath(Bd)
        self.flag = self.get_flag_enum(flag)

    def get_flag_enum(self, flag):
        if isinstance(flag, int):
            return flag

        if not isinstance(flag, str):
            raise NotImplementedError(flag)

        ret = self.__class__.__dict__.get(flag, None)
        if ret is None:
            raise NotImplementedError(flag)

        return ret

    def deside_image_save_dir(self,
                              album: Optional[JmAlbumDetail],
                              photo: JmPhotoDetail,
                              ) -> str:

        if photo is None:
            raise AssertionError('章节信息不能为None')

        def dirpath(album_dir: Optional[str], photo_dir: str):
            """
            @param album_dir: 相册文件夹名
            @param photo_dir: 章节文件夹名
            """
            from common import fix_windir_name
            photo_dir = fix_windir_name(photo_dir)

            if album_dir is None:
                return f'{self.Bd}{photo_dir}/'

            return f'{self.Bd}{album_dir}/{photo_dir}/'

        def photo_dir(flag_for_title):
            return photo.title if flag == flag_for_title else photo.photo_id

        flag = self.flag

        if flag in (0, 1):
            # 根目录 / Album作者 / Photo标题 / 图片文件
            # 根目录 / Album作者 / Photo号 / 图片文件

            author = album.author if album is not None else JmModuleConfig.default_author
            return dirpath(author, photo_dir(0))

        elif flag in (2, 3):
            # 根目录 / Album标题 / Photo标题 / 图片文件
            # 根目录 / Album标题 / Photo号 / 图片文件

            album_title = album.title if album is not None else photo.title
            return dirpath(album_title, photo_dir(2))

        elif flag in (4, 5):
            # 根目录 / Photo标题 / 图片文件
            # 根目录 / Photo号 / 图片文件

            return dirpath(None, photo_dir(4))

        else:
            if flag in self.additional_tree_flag_handler_mapping:
                return self.additional_tree_flag_handler_mapping[flag](album, photo)
            else:
                raise NotImplementedError

    @staticmethod
    def random_id():
        import common
        return common.time_stamp()

    @staticmethod
    def random_title():
        import common
        return common.format_ts(f_time="%Y-%m-%d-%H-%M-%S")

    @classmethod
    def accpet_flag_dict(cls):
        return dict(filter(lambda item: item[0].startswith('Bd_'),
                           cls.__dict__.items()))

    @classmethod
    def of(cls,
           tree_base_dir: str,
           tree_flag: int,
           ):
        for accpet_flag in cls.accpet_flag_dict().values():
            if accpet_flag is tree_flag:
                return DownloadDirTree(tree_base_dir, tree_flag)

        raise AssertionError(f'不支持的flag: {tree_flag}，'
                             f'请使用DownloadDirTree类字段中的值，或直接实例化DownloadDirTree对象')


class JmOption(SaveableEntity):
    _proxies_mapping = {
        'clash': ProxyBuilder.clash_proxy,
        'v2Ray': ProxyBuilder.v2Ray_proxy
    }

    when_del_save_file = False
    cache_jm_client = True

    def __init__(self,
                 dir_tree: DownloadDirTree,
                 client_config: dict,
                 use_tls_client=True,
                 filepath: StrNone = None,
                 disable_jm_module_debug=False,
                 download_use_disk_cache=True,
                 download_convert_image_suffix: StrNone = None,
                 download_image_then_decode=True,
                 download_multi_thread_photo_len_limit=30,
                 download_multi_thread_photo_batch_count=10,
                 ):

        # 请求配置
        self.use_tls_client = use_tls_client
        self.client_config = client_config
        self.client_config['postman_type_list'] = list(Postmans.postman_impl_class_dict.keys())

        # 下载配置
        self.dir_tree = dir_tree
        self.download_use_disk_cache = download_use_disk_cache
        self.download_image_then_decode = download_image_then_decode
        self.download_multi_thread_photo_len_limit = download_multi_thread_photo_len_limit
        self.download_multi_thread_photo_batch_count = download_multi_thread_photo_batch_count
        # suffix的标准形式是 ".xxx"。如果传入的是"xxx"，要补成 ".xxx"
        if download_convert_image_suffix is not None:
            download_convert_image_suffix = fix_suffix(download_convert_image_suffix)
        self.download_convert_image_suffix = download_convert_image_suffix

        # 其他配置
        self.filepath = filepath
        self.disable_jm_module_debug = disable_jm_module_debug
        if disable_jm_module_debug:
            disable_jm_debug()

    def decide_image_save_dir(self, album_detail, photo_detail) -> str:
        if album_detail is None and photo_detail is not None:
            album_detail = photo_detail.from_album

        dirpath = self.dir_tree.deside_image_save_dir(
            album_detail,
            photo_detail
        )
        mkdir_if_not_exists(dirpath)
        return dirpath

    def decide_image_filepath(self, photo_detail: JmPhotoDetail, index: int) -> str:
        dirpath = self.decide_image_save_dir(photo_detail.from_album, photo_detail)
        image = photo_detail[index]
        suffix = self.download_convert_image_suffix or image.img_file_suffix
        return dirpath + image.img_file_name + suffix

    @classmethod
    def default(cls) -> 'JmOption':
        return JmOption(
            DownloadDirTree(
                workspace(),
                DownloadDirTree.Bd_Title_Image,
            ),
            cls.default_client_config(),
        )

    @classmethod
    def create_from_file(cls, filepath: str) -> 'JmOption':
        jm_option = PackerUtil.unpack(filepath, JmOption)[0]
        jm_option.filepath = filepath
        return jm_option

    def save_base_dir(self):
        return of_dir_path(self.filepath)

    def save_file_name(self) -> str:
        return of_file_name(self.filepath)

    def save_to_file(self, filepath=None):
        if filepath is None:
            filepath = self.filepath

        if filepath is None:
            raise AssertionError("未指定JmOption的保存路径: self.filepath is None")

        super().save_to_file(filepath)

    # 下面是 build 方法

    def build_jm_client(self) -> JmcomicClient:
        if self.cache_jm_client is not True:
            client = self.new_jm_client()
        else:
            key = self
            client = JmModuleConfig.jm_client_caches.get(key, None)
            if client is None:
                client = self.new_jm_client()
                JmModuleConfig.jm_client_caches.setdefault(key, client)

        return client

    def new_jm_client(self) -> JmcomicClient:
        meta_data = self.client_config['meta_data']

        # 处理代理
        def handle_proxies(key='proxies'):
            proxies = meta_data.get(key, None)

            # 无代理，或代理已配置好好的
            if proxies is None or isinstance(proxies, dict):
                return

            # 有代理
            if proxies in self._proxies_mapping:
                proxies = self._proxies_mapping[proxies]()
            else:
                proxies = ProxyBuilder.build_proxy(proxies)

            meta_data[key] = proxies

        # 处理 headers
        def handle_headers(key='headers'):
            headers = meta_data.get(key, None)
            if headers is None or (not isinstance(headers, dict)) or len(headers) == 0:
                meta_data[key] = JmModuleConfig.default_headers()

        # 处理【特殊配置项】
        handle_proxies()
        handle_headers()

        # 决定Postman的实现类，根据配置项 client_config.postman
        postman_clazz = Postmans.get_impl_clazz(self.client_config.get('postman_type', 'cffi'))
        # 决定域名
        domain = self.client_config.get('domain', JmModuleConfig.DOMAIN)

        jm_debug('创建JmcomicClient', f'使用域名: {domain}，使用Postman实现: {postman_clazz}')
        # 创建 JmcomicClient 实例
        client = JmcomicClient(
            postman=postman_clazz(meta_data),
            domain=domain,
        )

        return client

    # 下面的方法是对【CdnOption】的支持

    def build_cdn_option(self, use_multi_thread_strategy=True):

        return CdnConfig.create(
            cdn_domain=self.client_config.get('domain', JmModuleConfig.DOMAIN),
            fetch_strategy=MultiThreadFetch if use_multi_thread_strategy else InOrderFetch,
            cdn_image_suffix=None,
            use_cache=self.download_use_disk_cache,
            decode_image=self.download_image_then_decode
        )

    def build_cdn_crawler(self, use_multi_thread_strategy=True):
        return CdnFetchService(self.build_cdn_option(use_multi_thread_strategy),
                               self.build_jm_client())

    def build_cdn_request(self,
                          photo_id: str,
                          scramble_id=str(JmModuleConfig.SCRAMBLE_10),
                          from_index=1,
                          photo_len=None,
                          use_default=False
                          ) -> CdnRequest:
        return CdnRequest.create(
            photo_id,
            self.build_save_path_provider(use_default, None if use_default else photo_id),
            scramble_id,
            from_index,
            photo_len,
        )

    def build_save_path_provider(self,
                                 use_all_default_save_path,
                                 photo_id=None,
                                 ) -> CdnRequest.SavePathProvider:

        if use_all_default_save_path is True:
            # 不通过请求获取 photo 的信息，相当于使用【空本子】和【空集】
            photo_detail, album_detail = None, None
        else:
            # 通过请求获得 photo 的本子信息
            client = self.build_jm_client()
            photo_detail = client.get_photo_detail(photo_id)
            album_detail = client.fill_from_album(photo_detail)

        suffix = self.download_convert_image_suffix

        def save_path_provider(url, _suffix: str, _index, _is_decode):
            return '{0}{1}{2}'.format(self.decide_image_save_dir(album_detail, photo_detail),
                                      of_file_name(url, trim_suffix=True),
                                      suffix or _suffix)

        return save_path_provider

    @classmethod
    def default_client_config(cls):
        """
        client_config:
          domain: 18comic.vip
          tls_session: null
          meta_data:
            cookies: null
            headers:
        """
        return {
            'domain': JmModuleConfig.DOMAIN,
            'tls_session': {
                'client_identifier': 'chrome_109',
            },
            'meta_data': {
                'cookies': None,
                'headers': JmModuleConfig.default_headers(),
                'allow_redirects': True,
            }
        }


def _register_yaml_constructor():
    from yaml import add_constructor, Loader, Node

    tag_mapping = {
        'tag:yaml.org,2002:python/object:jmcomic.jm_option.JmOption': JmOption,
        'tag:yaml.org,2002:python/object:jmcomic.jm_option.DownloadDirTree': DownloadDirTree,
    }

    def constructor(loader: Loader, node: Node):
        for tag, clazz in tag_mapping.items():
            if node.tag == tag:
                state = loader.construct_mapping(node)
                try:
                    obj = clazz(**state)
                except TypeError as e:
                    raise AssertionError(f"构造函数不匹配: {clazz.__name__}\nTypeError: {e}")

                # obj.__dict__.update(state)
                return obj

    for tag in tag_mapping.keys():
        add_constructor(tag, constructor)


_register_yaml_constructor()
