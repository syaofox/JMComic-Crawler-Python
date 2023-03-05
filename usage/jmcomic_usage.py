from jmcomic import *

use_proxy = "no"
# use_proxy = "use"
set_application_workspace(
    'D:/GitProject/dev/pip/crawler-jmcomic/assets/config'
)

jm_option = option(f'jmcomic_config_{use_proxy}_proxy.yml')


def str_to_list(lines: str):
    return [line.strip() for line in lines.strip().split('\n') if line.strip() != '']


# @disable
@timeit('下载本子集: ')
def download_jm_album():
    ls = str_to_list('''
    428165
    427413
    ''')

    multi_thread_launcher(
        iter_objs=((album_id, jm_option) for album_id in ls),
        apply_each_obj_func=download_album
    )


# @disable
@timeit('获取detail: ')
def get_album_photo_detail():
    client = jm_option.build_jm_client()
    album: JmAlbumDetail = client.get_album_detail('427413')

    def show(p):
        p: JmPhotoDetail = client.get_photo_detail(p.photo_id)
        print_list(p.data_original_list)

    multi_thread_launcher(
        iter_objs=album,
        apply_each_obj_func=show
    )


# @disable
@timeit('搜索本子: ')
def search_jm_album():
    client = jm_option.build_jm_client()
    search_album: JmSearchPage = client.search_album(search_query='+MANA +无修正')
    for album_id, title, *_args in search_album:
        print(f'[{album_id}]：{title}')


def main():
    search_jm_album()
    download_jm_album()
    get_album_photo_detail()


if __name__ == '__main__':
    main()
