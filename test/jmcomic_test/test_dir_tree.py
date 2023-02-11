from jmcomic_test import *


class Test_DirTree(JmTestConfigurable):

    def test_dir_tree(self):
        album_detail = JmAlbumDetail(None, None, 'album-title', [], 0, ['album-author'], '')
        photo_detail = JmPhotoDetail('6666', None, 'photo-title', [], [], '0', 'photo-author', None)

        for name, flag in DownloadDirTree.accpet_flag_dict().items():
            image_save_dir = DownloadDirTree.of(
                workspace(), flag
            ).deside_image_save_dir(album_detail, photo_detail)

            print(f"{name}: {image_save_dir}")
