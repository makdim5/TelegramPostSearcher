import asyncio
import threading
from datetime import datetime, timedelta
from kivy.lang import Builder
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.list import TwoLineAvatarIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.pickers import MDDatePicker
from telethon.sync import TelegramClient
from telethon.tl.types import Channel
from telethon.errors.rpcerrorlist import UsernameInvalidError

# Ваши API-данные Telegram
API_ID = 1234567 # !!! Замените на ваш api_id
API_HASH = 'your_api_hash' # !!! Замените на ваш api_hash
SESSION_NAME = 'my_kivy_session' # Имя файла сессии для Telethon

# KivyMD дизайн на языке KV
KV_CODE = """
MDBoxLayout:
    orientation: 'vertical'
    md_bg_color: self.theme_cls.bg_darkest

    
    MDBoxLayout:
        orientation: 'vertical'
        padding: "10dp"
        spacing: "10dp"
        size_hint_y: None
        height: self.minimum_height
        
        MDTextField:
            id: channel_input
            hint_text: "Имя канала (username), например: 'durov_channel'"
            helper_text: "Используйте @ для публичных каналов"
            pos_hint: {'center_x': 0.5}
            size_hint_x: 0.9

        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: "48dp"
            padding: "10dp", 0
            spacing: "10dp"
            pos_hint: {'center_x': 0.5}
            size_hint_x: 0.9

            MDTextField:
                id: keywords_input
                hint_text: "Ключевые слова через пробел"
                helper_text: "Например: 'искусственный интеллект'"
                size_hint_x: 0.85
            
            MDIconButton:
                icon: "magnify"
                on_release: app.start_search_button_with_keywords()
                size_hint_x: 0.15

        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: "48dp"
            padding: "10dp", 0
            spacing: "10dp"
            pos_hint: {'center_x': 0.5}
            size_hint_x: 0.9

            MDTextField:
                id: date_input
                hint_text: "Дата начала (YYYY-MM-DD)"
                pos_hint: {'center_y': 0.5}
                size_hint_x: 0.85
                readonly: True
            
            MDIconButton:
                icon: "calendar"
                pos_hint: {'center_y': 0.5}
                on_release: app.show_date_picker()
                size_hint_x: 0.15

        MDBoxLayout:
            orientation: 'horizontal'
            pos_hint: {'center_x': 0.5}
            size_hint_x: 0.9
            spacing: "10dp"
            padding: "10dp", 0

            MDLabel:
                text: "Тестовый режим (без Telethon)"
                pos_hint: {'center_y': 0.5}

            MDSwitch:
                id: test_mode_switch
                size_hint: None, None
                size: "48dp", "36dp"
                pos_hint: {'center_y': 0.5}
                on_active: app.toggle_test_mode(self.active)
        
        MDRaisedButton:
            id: search_button
            text: "Начать поиск"
            pos_hint: {'center_x': 0.5}
            size_hint_x: 0.9
            on_release: app.start_search()

    MDScrollView:
        id: scroll_view
        MDList:
            id: result_list
"""

class TelegramSearchApp(MDApp):
    dialog = None

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Dark"
        return Builder.load_string(KV_CODE)

    def on_start(self):
        self.root.ids.search_button.text = "Начать поиск"

    def show_dialog(self, title, text):
        if not self.dialog:
            self.dialog = MDDialog(
                title=title,
                text=text,
                buttons=[
                    MDFlatButton(
                        text="ОК",
                        on_release=self.close_dialog
                    ),
                ],
            )
        self.dialog.text = text
        self.dialog.title = title
        self.dialog.open()

    def close_dialog(self, inst):
        self.dialog.dismiss()

    def toggle_test_mode(self, active):
        if active:
            self.show_dialog("Тестовый режим", "Включен тестовый режим. Будут использоваться сгенерированные данные.")

    def show_date_picker(self):
        picker = MDDatePicker()
        picker.bind(on_save=self.on_date_selected)
        picker.open()

    def on_date_selected(self, instance, value, date_range):
        self.root.ids.date_input.text = value.strftime('%Y-%m-%d')

    def start_search(self):
        channel_name = self.root.ids.channel_input.text.strip()
        keywords_str = self.root.ids.keywords_input.text.strip()
        date_str = self.root.ids.date_input.text.strip()

        if not channel_name:
            self.show_dialog("Ошибка", "Пожалуйста, введите имя канала.")
            return
        
        self.root.ids.search_button.disabled = True
        self.root.ids.search_button.text = "Поиск..."
        self.root.ids.result_list.clear_widgets()

        is_test_mode = self.root.ids.test_mode_switch.active
        
        if is_test_mode:
            threading.Thread(
                target=lambda: asyncio.run(self.run_test_data_search(channel_name, keywords_str, date_str))
            ).start()
        else:
            threading.Thread(
                target=lambda: asyncio.run(self.run_telethon_search(channel_name, keywords_str, date_str))
            ).start()

    async def run_telethon_search(self, channel_name, keywords_str, date_str):
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        
        try:
            await client.start()
            
            try:
                entity = await client.get_entity(channel_name)
            except UsernameInvalidError:
                self.schedule_ui_update("Ошибка: Неверное имя канала. Проверьте правильность и публичность.", final=True)
                return
            except Exception as e:
                self.schedule_ui_update(f"Ошибка: Не удалось получить канал. {str(e)}", final=True)
                return
            
            start_date = None
            if date_str:
                try:
                    start_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    self.schedule_ui_update("Ошибка: Неверный формат даты. Используйте YYYY-MM-DD.", final=True)
                    return

            keywords = keywords_str.split()
            search_query = " ".join(keywords)

            found_count = 0
            async for message in client.iter_messages(entity, search=search_query):
                if start_date and message.date.date() < start_date:
                    break
                
                link = f"https://t.me/{channel_name}/{message.id}"
                self.schedule_ui_update(
                    f"Дата: {message.date.date()}\n{message.text[:200]}...",
                    link
                )
                found_count += 1
                
            self.schedule_ui_update(
                f"Поиск завершён. Найдено {found_count} постов.",
                final=True
            )
        except Exception as e:
            self.schedule_ui_update(f"Произошла ошибка: {str(e)}", final=True)
        finally:
            await client.disconnect()

    async def run_test_data_search(self, channel_name, keywords_str, date_str):
        # Имитация асинхронной работы и получения данных
        keywords = keywords_str.split()
        
        try:
            start_date = None
            if date_str:
                start_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            self.schedule_ui_update("Ошибка: Неверный формат даты. Используйте YYYY-MM-DD.", final=True)
            return

        mock_posts = [
            {"id": 101, "date": datetime(2025, 8, 25), "text": f"Тестовый пост о {keywords_str} #1"},
            {"id": 102, "date": datetime(2025, 8, 24), "text": "Важная новость о технологиях. Поиск по слову " + keywords[0]},
            {"id": 103, "date": datetime(2025, 8, 23), "text": "Обзор событий в мире " + keywords_str},
            {"id": 104, "date": datetime(2025, 8, 22), "text": "Старый пост, который не должен быть показан"},
            {"id": 105, "date": datetime(2025, 8, 21), "text": "Еще один пост с " + keywords[1]}
        ]
        
        found_count = 0
        for post in mock_posts:
            # Имитация задержки, чтобы показать, что это асинхронная операция
            await asyncio.sleep(0.5)
            
            # Фильтрация по дате
            if start_date and post["date"].date() < start_date:
                continue

            # Фильтрация по ключевым словам (простая проверка)
            if not all(k.lower() in post["text"].lower() for k in keywords):
                continue

            self.schedule_ui_update(
                f"Дата: {post['date'].date()}\n{post['text']}",
                f"https://t.me/{channel_name}/{post['id']}"
            )
            found_count += 1
        
        self.schedule_ui_update(
            f"Тестовый поиск завершён. Найдено {found_count} постов.",
            final=True
        )

    def schedule_ui_update(self, text, link=None, final=False):
        Clock.schedule_once(
            lambda dt: self.update_ui(text, link, final)
        )

    def update_ui(self, text, link, final):
        if final:
            self.root.ids.search_button.disabled = False
            self.root.ids.search_button.text = "Начать поиск"
            self.root.ids.result_list.add_widget(
                TwoLineAvatarIconListItem(
                    text=text,
                    bg_color=self.theme_cls.primary_color,
                    _no_ripple_effect=True
                )
            )
        elif link:
            self.root.ids.result_list.add_widget(
                TwoLineAvatarIconListItem(
                    text=f"[b]Пост:[/b] {link}",
                    secondary_text=text,
                    _no_ripple_effect=True,
                    on_release=lambda x: self.copy_link(link)
                )
            )
    
    def copy_link(self, link):
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(link)
        self.show_dialog("Копирование", "Ссылка скопирована в буфер обмена!")

if __name__ == '__main__':
    TelegramSearchApp().run()