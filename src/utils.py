from kivymd.uix.snackbar import MDSnackbar, MDSnackbarSupportingText
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogIcon,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
    MDDialogContentContainer,
)
from kivymd.uix.textfield import (
    MDTextField,
    MDTextFieldLeadingIcon,
    MDTextFieldHintText,
    MDTextFieldTrailingIcon,
)
from kivymd.uix.progressindicator.progressindicator import MDCircularProgressIndicator
from kivymd.uix.list.list import (
    MDList,
    MDListItem,
    MDListItemLeadingIcon,
    MDListItemHeadlineText,
    MDListItemSupportingText,
    MDListItemTertiaryText,
    MDListItemTrailingIcon,
)
from kivymd.uix.scrollview import MDScrollView

from dataclasses import dataclass
from datetime import datetime, date
import os
import webbrowser
import pyperclip
from telethon.sync import TelegramClient
from telethon.tl.types import Channel


@dataclass
class TelegramCredentials:
    id: str = ""
    hash: str = ""


@dataclass
class TelegramPost:
    id: str
    channel_name: str
    channel_title: str
    date: datetime
    text: str

    @property
    def uri(self):
        return f"https://t.me/{self.channel_name}/{self.id}"


TEMP_POSTS = [
    TelegramPost(
        "1",
        "bcz_kostyukovichi",
        "БЦЗ Костюковичи",
        datetime(2025, 6, 4, 2),
        "У истоков завода…",
    ),
    TelegramPost(
        "2", "rozetked", "Rozetked", datetime(2025, 9, 17, 2), "Iphone 17 pro …"
    ),
    TelegramPost(
        "2",
        "sweden_live",
        "Швеция ЖЫЗА",
        datetime(2025, 9, 20, 7),
        "haha Iphone 16 pro AI …",
    ),
]


def show_snack_bar(text: str) -> None:
    MDSnackbar(
        MDSnackbarSupportingText(
            text=text,
        ),
        orientation="horizontal",
        pos_hint={"center_x": 0.5},
        size_hint_x=0.5,
    ).open()


def show_alert_dialog(headline: str, text: str = "") -> None:
    dialog = MDDialog(
        MDDialogIcon(
            icon="alert-circle-outline",
        ),
        MDDialogHeadlineText(
            text=headline,
        ),
        MDDialogSupportingText(
            text=text,
        ),
        MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(text="Close"),
                style="text",
                on_release=lambda e: dialog.dismiss(),
            ),
            spacing="8dp",
        ),
    )

    dialog.open()


def show_wait_dialog() -> MDDialog:
    dialog = MDDialog(
        MDDialogIcon(icon="update"),
        MDDialogHeadlineText(text="Wait, please ..."),
        MDDialogContentContainer(
            Widget(),
            MDCircularProgressIndicator(
                size_hint=(None, None), size=(dp(50), dp(50)), active=True
            ),
            Widget(),
        ),
    )

    dialog.open()

    return dialog


def show_settings_dialog(app) -> None:
    def clear_keywords_list():
        app.keywords.clear()
        show_snack_bar("Очищено!")
        app.create_selectors()

    def clear_sources_list():
        app.sources.clear()
        show_snack_bar("Очищено!")
        app.create_selectors()

    def on_close():
        dialog.dismiss()
        app.creds = TelegramCredentials(id_text_field.text, hash_text_field.text)

    id_text_field = MDTextField(
        MDTextFieldLeadingIcon(
            icon="magnify",
        ),
        MDTextFieldHintText(
            text="Telegram ID",
        ),
        MDTextFieldTrailingIcon(
            icon="information",
        ),
        mode="outlined",
    )

    id_text_field.text = app.creds.id

    hash_text_field = MDTextField(
        MDTextFieldLeadingIcon(
            icon="magnify",
        ),
        MDTextFieldHintText(
            text="Telegram Hash",
        ),
        MDTextFieldTrailingIcon(
            icon="information",
        ),
        mode="outlined",
    )

    hash_text_field.text = app.creds.hash

    dialog = MDDialog(
        MDDialogIcon(
            icon="google-nearby",
        ),
        MDDialogHeadlineText(
            text="Настройки",
        ),
        MDDialogContentContainer(
            MDButton(
                MDButtonText(text="Очистить список ключевых слов"),
                on_release=lambda e: clear_keywords_list(),
            ),
            MDButton(
                MDButtonText(text="Очистить список каналов"),
                on_release=lambda e: clear_sources_list(),
            ),
            id_text_field,
            hash_text_field,
            orientation="vertical",
            spacing=dp(10),
        ),
        MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(text="Закрыть"),
                style="text",
                on_release=lambda e: on_close(),
            ),
            spacing="8dp",
        ),
    )

    dialog.open()


def transform_posts_into_list_view(posts: list[TelegramPost]):
    list_view = MDList()

    for post in posts:
        list_view.add_widget(
            MDListItem(
                MDListItemLeadingIcon(
                    icon="star",
                ),
                MDListItemHeadlineText(
                    text=post.id + " " + str(post.date),
                ),
                MDListItemSupportingText(
                    text=post.text,
                ),
                MDListItemTertiaryText(
                    text=post.uri,
                ),
                MDIconButton(
                    icon="content-copy",
                    on_release=lambda x, y=post: pyperclip.copy(y.uri),
                ),
                MDIconButton(
                    icon="google-chrome",
                    on_release=lambda x, y=post: webbrowser.open(y.uri),
                ),
            )
        )

    return MDScrollView(list_view, do_scroll_x=False)


def export_post_to_ms_word(posts: list[TelegramPost]):
    script = "\n".join(
        [
            'Set wdApp = CreateObject("Word.Application")',
            "wdApp.Visible = True",
            'Set fso = CreateObject("Scripting.FileSystemObject")',
            "scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)",
            'docPath = scriptPath & "\\" & "assets\\msword_templates\\template.docx"',
            "Set wdDoc = wdApp.Documents.Open(docPath)",
            "Set tbl = wdDoc.Tables(1)",
        ]
    )

    def transform_post_to_word_string(post: TelegramPost):
        return "".join(
            [
                f'"{item}" & vbCrLf & '
                for item in [
                    str(post.date.date()),
                    post.uri,
                    post.text.replace("\n", " "),
                ]
            ]
        )[:-2]

    for post in posts:
        script += f"\ntbl.Rows.Add\ntbl.Cell(tbl.Rows.Count, tbl.Columns.Count).Range.Text = {transform_post_to_word_string(post)}\n"

    with open("run_template.vbs", mode="w", encoding="utf-16") as f:
        f.write(script)

    os.system("run_template.vbs")


def open_instruction():
    script = "\n".join(
        [
            'Set wdApp = CreateObject("Word.Application")',
            "wdApp.Visible = True",
            'Set fso = CreateObject("Scripting.FileSystemObject")',
            "scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)",
            'docPath = scriptPath & "\\" & "assets\\msword_templates\\instruction.docx"',
            "Set wdDoc = wdApp.Documents.Open(docPath)",
        ]
    )

    with open("open_doc.vbs", mode="w", encoding="utf-16") as f:
        f.write(script)

    os.system("open_doc.vbs")


def search_posts_with_links(
    creds: TelegramCredentials, channel_name: str, keywords: list[str], start_date: date
):
    with TelegramClient("my_session", creds.id, creds.hash) as client:
        try:
            channel = client.get_entity(channel_name)
            if not isinstance(channel, Channel):
                print(f"Ошибка: {channel_name} не является каналом.")
                return
        except ValueError as e:
            print(f"Ошибка при поиске канала: {e}")
            return

        posts = []

        for message in client.iter_messages(channel, search=" ".join(keywords)):
            if message.text and message.date.date() > start_date:
                posts.append(
                    TelegramPost(
                        str(message.id),
                        channel_name,
                        channel.title,
                        message.date,
                        message.text,
                    )
                )

        return posts
