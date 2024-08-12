##############################
#  기본 환경 설정
##############################
import os
from dotenv import load_dotenv
load_dotenv()

####################################################################
#  Chainlit 인증
#  터미널에서 `chainlit create-secret` 명령어를 사용하여 비밀번호를 생성하고,
#  .env 파일에 CHAINLIT_AUTH_SECRET 키를 추가해야 합니다.
####################################################################
import sqlite3
import hashlib
import chainlit as cl
from typing import Optional

@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    # SQLite 연결
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()

    # 사용자 정보 가져오기
    cursor.execute('SELECT password, role FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        stored_password, role = result
        # 비밀번호 해싱
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        # 비밀번호 비교
        if hashed_password == stored_password:
            return cl.User(
                identifier=username, metadata={"role": role, "provider": "credentials"}
            )
    return None

##############################
#  LCEL Chain
##############################
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable
from langchain_core.runnables.config import RunnableConfig

import chainlit as cl

# 채팅 세션이 시작될 때 호출되는 함수 등록
@cl.on_chat_start
async def on_chat_start():
    # 사용자 정보 가져오기
    app_user = cl.user_session.get("user")
    await cl.Message(f"Hello {app_user.identifier}").send()

    # 스트리밍이 활성화된 ChatOpenAI 모델 초기화
    model = ChatOpenAI(model="gpt-4o-mini", max_tokens=100, streaming=True)
    
    # 프롬프트 템플릿 생성
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You're a helpful assistant."),
            ("human", "{question}"),  
        ]
    )
    
    # 프롬프트 템플릿, 모델, 출력 파서를 연결하여 runnable 생성
    runnable = prompt | model | StrOutputParser()
    
    # runnable을 현재 사용자 세션에 설정
    cl.user_session.set("runnable", runnable)

# 사용자가 메시지를 보낼 때 호출되는 함수 등록
@cl.on_message
async def on_message(message: cl.Message):
    # 현재 사용자 세션에서 runnable 가져오기
    runnable = cl.user_session.get("runnable")  # type: Runnable
    
    # 빈 콘텐츠로 새로운 메시지 객체 생성
    msg = cl.Message(content="")
    
    # runnable의 비동기 스트리밍 응답 처리
    async for chunk in runnable.astream(
        {"question": message.content},  # 사용자 질문 전달
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),  # 콜백 핸들러 설정
    ):
        await msg.stream_token(chunk)  # 스트리밍된 청크를 msg 객체에 추가
    
    # 완성된 메시지 전송
    await msg.send()

##############################
# Chainlit 애플리케이션 실행
##############################
if __name__ == "__main__":
    cl.run()
