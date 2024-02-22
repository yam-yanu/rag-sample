import os
from time import sleep
from typing import Optional

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.beta.threads import ThreadMessage

load_dotenv()


class AssistantClient:
    _assistant_id: str
    thread_id: Optional[str]

    def __init__(self, assistant_id: str, thread_id: Optional[str]):
        self._assistant_id = assistant_id
        self.thread_id = thread_id

    def initialize_thread(self):
        thread = OpenAI().beta.threads.create()
        print(f'ID: {thread.id} のスレッドを作成しました。')
        self.thread_id = thread.id

    def fetch_messages(self) -> list[ThreadMessage]:
        if not self.thread_id:
            return []
        try:
            return OpenAI().beta.threads.messages.list(
                thread_id=self.thread_id,
                order='asc',
            ).data
        except Exception:
            return []

    def create_user_message(self, prompt: str) -> ThreadMessage:
        if not self.thread_id:
            self.initialize_thread()
        return OpenAI().beta.threads.messages.create(
            thread_id=self.thread_id,
            role='user',
            content=prompt
        )

    def generate_assistant_messages(self, user_message_id: str) -> list[ThreadMessage]:
        if not self.thread_id:
            raise Exception('Thread IDを初期化していないのでアシスタントを動かせません。')
        run = OpenAI().beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self._assistant_id,
        )
        while run.status in ["queued", "in_progress"]:
            sleep(2)
            run = OpenAI().beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=run.id,
            )
        return OpenAI().beta.threads.messages.list(
            thread_id=self.thread_id,
            order='asc',
            after=user_message_id,
        )


st.title("工業製品FAQ")

client = AssistantClient(
    os.environ['APP2_OPENAI_API_ASSISTANT_ID'],
    st.session_state.thread_id if 'thread_id' in st.session_state else None,
)

# メッセージの初期化
if 'messages' not in st.session_state:
    st.session_state.messages = client.fetch_messages()
for message in st.session_state.messages:
    st.chat_message(message.role).markdown(message.content[0].text.value)

if prompt := st.chat_input():
    # ユーザーのメッセージ
    user_message = client.create_user_message(prompt)
    st.chat_message("user").markdown(prompt)

    # アシスタントを実行し、終わるのを待つ
    with st.spinner('回答中...'):
        new_messages = client.generate_assistant_messages(user_message.id)
    for m in new_messages:
        st.chat_message(m.role).markdown(m.content[0].text.value)

    # 次のラウンドのために状態を保存
    st.session_state.messages = [*st.session_state.messages, user_message, *new_messages]
    st.session_state.thread_id = client.thread_id

