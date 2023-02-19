from common import multi_thread_launcher

from .jm_option import *
from .jm_toolkit import *


def build_client(option: Optional[JmOption]) -> Tuple[JmOption, JmcomicClient]:
    """
    处理option的判空，并且创建jm_client
    """
    option = option or JmOption.default()
    jm_client = option.build_jm_client()
    return option, jm_client


def option(option_filepath: str, use_workspace=True) -> JmOption:
    """
    创建JmOption的api
    """
    if use_workspace is True:
        option_filepath = workspace(option_filepath)

    return JmOption.create_from_file(option_filepath)


def download_album(jm_album_id, option=None):
    """
    下载一个本子集，入口api
    """
    option, jm_client = build_client(option)
    album_detail: JmAlbumDetail = jm_client.get_album_detail(jm_album_id)

    jm_debug('download_album',
             f'获得album_detail成功，准备下载。'
             f'本子作者是【{album_detail.author}】，一共有{len(album_detail)}集本子')

    def download_photo(index, photo_detail: JmPhotoDetail, debug_topic='download_album_photo'):
        jm_client.fill_photo_data_original(photo_detail)

        jm_debug(debug_topic,
                 f"下载第[{index + 1}]集: "
                 f"图片数为[{len(photo_detail)}]，"
                 f"标题为：({photo_detail.title}) "
                 f"-- photo {photo_detail.photo_id}")

        download_by_photo_detail(
            photo_detail,
            option,
        )

        jm_debug(debug_topic,
                 f"下载完成：({photo_detail.title}) -- photo {photo_detail.photo_id}")

    multi_thread_launcher(
        iter_objs=enumerate(album_detail),
        apply_each_obj_func=download_photo,
        wait_finish=True,
    )


def download_photo(jm_photo_id, option=None):
    """
    下载一个本子的一章，入口api
    """
    option, jm_client = build_client(option)
    photo_detail = jm_client.get_photo_detail(jm_photo_id)
    download_by_photo_detail(photo_detail, option)


def download_by_photo_detail(photo_detail: JmPhotoDetail,
                             option=None,
                             ):
    """
    下载一个本子的一章，根据 photo_detail
    @param photo_detail: 本子章节信息
    @param option: 选项
    """
    option, jm_client = build_client(option)

    # 下载准备
    use_cache = option.download_use_disk_cache
    decode_image = option.download_image_then_decode

    # 下载每个图片的函数
    def download_image(index, debug_topic='download_images_of_photo'):
        img_detail = photo_detail[index]
        img_save_path = option.decide_image_filepath(photo_detail, index)

        # 已下载过，缓存命中
        if use_cache is True and file_exists(img_save_path):
            jm_debug(debug_topic, f'photo-{img_detail.aid}: '
                                  f'图片{img_detail.filename}已下载过，'
                                  f'命中磁盘缓存（{img_detail.img_url}）')
            return

        # 开始下载
        jm_client.download_by_image_detail(
            img_detail,
            img_save_path,
            decode_image=decode_image,
        )
        jm_debug(debug_topic, f'photo-{img_detail.aid}: '
                              f'图片{img_detail.filename}下载完成：'
                              f'[{img_detail.img_url}] → [{img_save_path}]')

    length = len(photo_detail)
    # 根据图片数，决定下载策略
    if length <= option.download_multi_thread_photo_len_limit:
        # 如果图片数小的话，直接使用多线程下载，一张图一个线程。
        multi_thread_launcher(
            iter_objs=range(len(photo_detail)),
            apply_each_obj_func=download_image,
            wait_finish=True
        )
    else:
        # 如果图片数多的话，还是分批下载。
        batch_count = option.download_multi_thread_photo_batch_count
        batch_times = length // batch_count

        for i in range(batch_times):
            begin = i * batch_count
            multi_thread_launcher(
                iter_objs=range(begin, begin + batch_count),
                apply_each_obj_func=download_image,
            )

        multi_thread_launcher(
            iter_objs=range(batch_times * batch_count,
                            length),
            apply_each_obj_func=download_image,
        )
