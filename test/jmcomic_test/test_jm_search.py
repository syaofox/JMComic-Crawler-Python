from jmcomic_test import *


class Test_Search(JmTestConfigurable):

    def setUp(self):
        self.set_workspace_to_resources_dir()

    def test_analyse_search_html(self):
        test_file = "search-html.txt"
        html = read_text(workspace(test_file))

        # (album_id, title, category_none, label_sub_none, tag_list)
        for i, line in enumerate(JmSearchPattern.analyse_jm_search_html(html)):
            print(f'index: {i}--------------------------------------------------------\n'
                  f'id: {line[0]}\n'
                  f'title: {line[1]}\n'
                  f'category_none: {line[2]}\n'
                  f'label_sub_none: {line[3]}\n'
                  f'tag_list: {line[4]}\n\n'
                  )
