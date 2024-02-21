import os
from time import sleep

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

assistant_id = os.environ['OPENAI_API_ASSISTANT_ID']

st.title("会計FAQチャットボット")


def initialize_thread() -> str:
    thread = OpenAI().beta.threads.create()
    st.session_state.thread_id = thread.id
    return thread.id


# threadがない場合threadの初期化
if "thread_id" not in st.session_state:
    thread_id = initialize_thread()
else:
    thread_id = st.session_state.thread_id

# threadが無効の場合も初期化
try:
    messages = OpenAI().beta.threads.messages.list(
        thread_id=thread_id,
        order='asc',
    )
    print(f'thread already exists. \n {thread_id}')
except Exception as e:
    thread_id = initialize_thread()
    print(f'thread created. \n {thread_id}')
    messages = []

for message in messages:
    st.chat_message(message.role).markdown(message.content[0].text.value)

if prompt := st.chat_input():
    # ユーザーのメッセージ
    user_message = OpenAI().beta.threads.messages.create(
        thread_id=thread_id,
        role='user',
        content=prompt
    )
    st.chat_message("user").markdown(prompt)

    # アシスタントを実行し、終わるのを待つ
    with st.spinner('回答中...'):
        run = OpenAI().beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )
        while run.status in ["queued", "in_progress"]:
            sleep(2)
            run = OpenAI().beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id,
            )
        new_messages = OpenAI().beta.threads.messages.list(
            thread_id=thread_id,
            order='asc',
            after=user_message.id,
        )
    for m in new_messages:
        print(m.content)
        st.chat_message(m.role).markdown(m.content[0].text.value)
