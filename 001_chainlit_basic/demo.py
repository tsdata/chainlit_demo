from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable
from langchain_core.runnables.config import RunnableConfig

import chainlit as cl

from dotenv import load_dotenv
load_dotenv()


# 채팅 세션이 시작될 때 호출되는 함수 등록
@cl.on_chat_start
async def on_chat_start():
    # 스트리밍이 활성화된 ChatOpenAI 모델 초기화
    model = ChatOpenAI(model="gpt-4o-mini", streaming=True)
    
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