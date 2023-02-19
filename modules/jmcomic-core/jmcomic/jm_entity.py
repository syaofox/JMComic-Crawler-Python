from .jm_config import *


class JmBaseEntity:
    pass


class WorkEntity(JmBaseEntity, SaveableEntity, IterableEntity):
    when_del_save_file = False
    after_save_print_info = True
    attr_char = '_'

    cache_getitem_result = True
    cache_field_name = '__cache_items_dict__'
    detail_save_base_dir = workspace()

    def save_base_dir(self):
        return self.detail_save_base_dir

    def save_file_name(self) -> str:
        return f"【{self.get_id_prefix_of_filename()}{self.get_id()}】{self.get_title()}.json"

    def get_id_prefix_of_filename(self):
        # "JmAlbumDetail" -> "album"
        cls_name = self.__class__.__name__
        id_prefix = cls_name[cls_name.index("m") + 1: cls_name.rfind("Detail")]
        return f'{id_prefix}-'

    def get_id(self) -> str:
        raise NotImplementedError

    def get_title(self) -> str:
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError

    def __getitem__(self, item):
        raise NotImplementedError


class JmImageDetail(JmBaseEntity):

    def __init__(self,
                 aid,
                 scramble_id,
                 img_url,
                 img_file_name,
                 img_file_suffix,
                 from_photo=None,
                 ) -> None:
        self.aid: str = aid
        self.scramble_id: str = scramble_id
        self.img_url: str = img_url
        self.img_file_name: str = img_file_name
        self.img_file_suffix: str = img_file_suffix

        self.from_photo: Optional[JmPhotoDetail] = from_photo

    @property
    def filename(self):
        return self.img_file_name + self.img_file_suffix

    @classmethod
    def of(cls,
           photo_id: str,
           scramble_id: str,
           data_original: str,
           from_photo=None,
           ) -> 'JmImageDetail':
        """
        该方法用于创建 JmImageDetail 对象
        """

        # /xxx.yyy
        # ↑   ↑
        # x   y
        x = data_original.rfind('/')
        y = data_original.rfind('.')

        return JmImageDetail(
            aid=photo_id,
            scramble_id=scramble_id,
            img_url=data_original,
            img_file_name=data_original[x + 1:y],
            img_file_suffix=data_original[y:],
            from_photo=from_photo,
        )


class JmPhotoDetail(WorkEntity):

    def __init__(self,
                 photo_id,
                 scramble_id,
                 title,
                 data_original_list,
                 keywords,
                 series_id,
                 author=None,
                 from_album=None,
                 ):
        self.photo_id: str = photo_id
        self.scramble_id: str = scramble_id
        self.title: str = title
        self._keywords: str = keywords
        self._series_id: int = int(series_id)

        self._author: StrNone = author
        self.data_original_list: Optional[list] = data_original_list
        self.from_album: Optional[JmAlbumDetail] = from_album

    def is_single_album(self) -> bool:
        return self._series_id == 0

    @property
    def keyword_list(self) -> List[str]:
        return self._keywords.split(',')

    @property
    def album_id(self) -> str:
        return self.photo_id if self.is_single_album() else self._series_id

    @property
    def author(self) -> str:
        # self._author 不为空字符串
        if self._author is not None and self._author != '':
            return self._author.strip()

        # self._author 为空，先向上找
        if self.from_album is not None:
            return self.from_album.author

        # 无向上元素，使用默认
        return JmModuleConfig.default_author

    def create_image_detail(self, index) -> JmImageDetail:
        # 校验参数
        length = len(self.data_original_list)
        if index >= length:
            raise AssertionError(f'创建JmImageDetail失败，{index} >= {length}')

        data_original = self.data_original_list[index]

        return JmImageDetail.of(
            self.photo_id,
            self.scramble_id,
            data_original,
            from_photo=self
        )

    def __getitem__(self, item) -> JmImageDetail:
        return self.create_image_detail(item)

    def get_id(self):
        return self.photo_id

    def get_title(self):
        return self.title

    def __len__(self):
        return len(self.data_original_list)


class JmAlbumDetail(WorkEntity):

    def __init__(self,
                 album_id,
                 scramble_id,
                 title,
                 episode_list,
                 page_count,
                 author_list,
                 pub_date,
                 ):
        self.album_id: str = album_id
        self.scramble_id: str = scramble_id
        self.title: str = title
        self.page_count = int(page_count)
        self._author_list: List[str] = author_list
        self.pub_date = pub_date

        # 有的 album 没有章节，则自成一章。
        if len(episode_list) == 0:
            # photo_id, photo_index_of_album, photo_title, photo_pub_date
            episode_list = [(album_id, 0, title, pub_date)]

        self.episode_list: List[Tuple] = episode_list

    def create_photo_detail(self, index) -> Tuple[JmPhotoDetail, Tuple]:
        # 校验参数
        length = len(self.episode_list)

        if index >= length:
            raise AssertionError(f'创建JmPhotoDetail失败，{index} >= {length}')

        # episode_info: ('212214', '81', '94 突然打來', '2020-08-29')
        episode_info: tuple = self.episode_list[index]
        photo_id, photo_index_of_album, photo_title, photo_pub_date = episode_info

        photo_detail = JmPhotoDetail(
            photo_id=photo_id,
            scramble_id=self.scramble_id,
            title=photo_title,
            data_original_list=[],
            keywords='',
            series_id=self.album_id,
            author=self.author,
            from_album=self,
        )

        return photo_detail, episode_info

    @property
    def author(self):
        if len(self._author_list) >= 1:
            return self._author_list[0]
        return JmModuleConfig.default_author

    def get_id(self):
        return self.album_id

    def get_title(self):
        return self.title

    def __len__(self):
        return len(self.episode_list)

    def __getitem__(self, item) -> JmPhotoDetail:
        return self.create_photo_detail(item)[0]


class JmSearchPage(IterableEntity):

    def __init__(self, album_info_list) -> None:
        # (album_id, title, category_none, label_sub_none, tag_list)
        self.data: List[Tuple[str, str, StrNone, StrNone, List[str]]] = album_info_list

    def album_id_iter(self) -> Iterable[str]:
        for album_info in self.data:
            yield album_info[0]

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        return self.data[item]


# cdn爬取请求
class CdnRequest:
    SavePathProvider = Callable[[str, str, int, bool], str]

    def __init__(self,
                 photo_id,
                 scramble_id,
                 from_index: int,
                 photo_len: Optional[int],
                 save_path_provider: SavePathProvider,
                 ):
        self.photo_id = photo_id
        self.scramble_id = scramble_id
        self.from_index = from_index
        self.photo_len = photo_len
        self.save_path_provider = save_path_provider

    @classmethod
    def create(cls,
               photo_id,
               save_path_provider: SavePathProvider,
               scramble_id,
               from_index=1,
               photo_len=None,
               ):
        return CdnRequest(
            photo_id,
            scramble_id,
            from_index,
            photo_len,
            save_path_provider,
        )
