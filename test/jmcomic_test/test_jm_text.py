from jmcomic_test import *


class Test_Text(JmTestConfigurable):

    @classmethod
    def setUpClass(cls, **kwargs):
        super().setUpClass(**kwargs)
        cls.set_workspace_to_resources_dir()

    def test_analyse_photo_html(self):
        with workspace('a.txt', 'r') as f:
            print(JmcomicText.analyse_jm_photo_html(f.read()))

    def test_analyse_album_html(self):
        with workspace('album-html.txt', 'r') as f:
            album_detail: JmAlbumDetail = JmcomicText.analyse_jm_album_html(f.read())

            album_detail.cache_getitem_result = True
            album_detail.when_del_save_file = False
            JmPhotoDetail.when_del_save_file = False

            print_list(album_detail.episode_list)
            # photo_detail: JmPhotoDetail = album_detail[0]

    def test_regex(self):
        template = "({kkk}{a}*?)*{a}({a}*?{kkk})*?"

        replacement = {
            "kkk": '<span itemprop="author" data-type="author">',
            "a": '(\n<a name="vote_\d+".*?>(.*?)</a>)'
        }

        template = template.format(**replacement)

        copy_to_clip(template, do_print=True)

    def test_regex_author(self):
        html_text = read_text(workspace("album-html.txt"))
        album_detail: JmAlbumDetail = JmcomicText.analyse_jm_album_html(html_text)
        print(album_detail._author_list)
