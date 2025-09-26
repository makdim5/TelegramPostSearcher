import os
import json

from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.pickers import MDModalDatePicker

import src.utils as utils


class PostsApp(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.keywords = []
        self.sources = []
        self.creds = utils.TelegramCredentials()

        self.posts = []
        self.search_date = None

        self._default_config_path = "cache.json"

    def on_start(self):
        config = {"id": "", "hash": "", "keywords": [], "sourses": []}

        if os.path.exists(self._default_config_path):
            with open(self._default_config_path) as f:
                config = json.load(f)

        self.keywords = config.get("keywords", [])
        self.sources = config.get("sources", [])
        self.creds = utils.TelegramCredentials(
            config.get("id", ""), config.get("hash", "")
        )

        self.create_selectors()

        self.not_found_widgets = [
            self.root.ids.not_found_img,
            self.root.ids.not_found_btn,
        ]

    def on_stop(self):
        with open(self._default_config_path, mode="w") as f:
            json.dump(
                {
                    "id": self.creds.id,
                    "hash": self.creds.hash,
                    "keywords": self.keywords,
                    "sources": self.sources,
                },
                f,
                indent=4,
            )

    def on_settings_btn_click(self):
        utils.show_settings_dialog(self)

    def create_selectors(self):
        self.source_selector = MDDropdownMenu(
            caller=self.root.ids.source_selector,
            items=[
                {
                    "text": item,
                    "on_release": lambda x=item: self._on_selector_item_clicked(
                        x, self.root.ids.source_text_field, self.source_selector
                    ),
                }
                for item in self.sources
            ],
        )

        self.key_words_selector = MDDropdownMenu(
            caller=self.root.ids.key_words_selector,
            items=[
                {
                    "text": item,
                    "on_release": lambda x=item: self._on_selector_item_clicked(
                        x, self.root.ids.key_words_text_field, self.key_words_selector
                    ),
                }
                for item in self.keywords
            ],
        )

    def _on_selector_item_clicked(self, text_item, text_control, menu_control):
        menu_control.dismiss()
        text_control.text = text_item

    def build(self):
        return Builder.load_file("src/ui.kv")

    def on_select_day(self, instance_date_picker):
        instance_date_picker.dismiss()
        utils.show_snack_bar(f"Выбранный день {instance_date_picker.get_date()[0]}")
        self.root.ids.date_btn_label.text = str(instance_date_picker.get_date()[0])
        self.search_date = instance_date_picker.get_date()[0]

    def show_modal_date_picker(self, *args):
        date_dialog = MDModalDatePicker()
        date_dialog.bind(on_ok=self.on_select_day)
        date_dialog.open()

    def open_instruction(self):
        utils.show_snack_bar("Открываем файл с инструкцией ...")
        utils.open_instruction()

    def search(self):
        if self.root.ids.source_text_field.text not in self.sources:
            self.sources.append(self.root.ids.source_text_field.text)

        if self.root.ids.key_words_text_field.text not in self.keywords:
            self.keywords.append(self.root.ids.key_words_text_field.text)

        self.create_selectors()
        self.root.ids.posts_container.clear_widgets()
        utils.show_snack_bar("Поиск начался ...")

        try:
            self.posts = utils.search_posts_with_links(
                self.creds,
                self.root.ids.source_text_field.text,
                self.root.ids.key_words_text_field.text.split(),
                self.search_date,
            )

            self.root.ids.posts_container.add_widget(
                utils.transform_posts_into_list_view(self.posts)
            )
        except Exception as e:
            utils.show_alert_dialog("Ошибка", "Посты не могут быть найдены!")

        if not self.posts:
            for item in self.not_found_widgets:
                self.root.ids.posts_container.add_widget(item)

    def post_export_to_word(self):
        utils.show_snack_bar("Экспорт постов в MS Word начался ...")
        utils.export_post_to_ms_word(self.posts)
