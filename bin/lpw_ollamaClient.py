import streamlit as st
from openai import OpenAI
from typing import List
import os

class OllamaClient():

    def __init__(self, server="127.0.0.1"):
        self.messages = []
        self.client = OpenAI(
            base_url=f'http://{server}:11434/v1',
            api_key=os.getenv('OPENAI_API_KEY')
        )

    def setServer(self, server, port):
        self.client = OpenAI(
            base_url=f'http://{server}:{port}/v1',
            api_key=os.getenv('OPENAI_API_KEY')
        )
    
    def clear_history(self):
        self.messages.clear()
    
    def append_history(self, message):
        self.messages.append(message)
    
    def check_system_message(self) -> bool:
        try:
            if self.messages[0]['role'] == 'system':
                return True
            else:
                return False
        except:
            return False
    
    def set_system_message(self, system_message:str) -> None:
        if self.check_system_message():
            self.edit_system_message(system_message)
        else:
            self.create_system_message(system_message)
    
    def create_system_message(self, system_message:str) -> None:
        sMessage = dict({'role' : 'system', 'content' : system_message})
        self.messages.append(sMessage)

    def edit_system_message(self, system_message:str) -> None:
        for m in self.messages:
            if m['role'] == 'system':
                m['content'] = system_message
    
    def chat(self, prompt:str, model: str, temp: float, system:str = "default") -> str:
        message = {}
        message['role'] = 'user'
        message['content'] = prompt
        self.messages.append(message)
        response = None
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=self.messages,
                temperature=temp
            )
        except Exception as e:
            st.error(f'Error Occured : {e} ', icon="🚨")
            st.stop()
        assistant_message = {
            'role': 'assistant',
            'content': response.choices[0].message.content
        }
        self.messages.append(assistant_message)
        return response.choices[0].message.content

    def chat_stream(self, prompt:str, model: str, temp: float, system:str = "default"):
        message = {}
        stream = None
        if system != 'default' and not self.check_system_message():
            sMessage = dict({'role' : 'system', 'content' : system})
            self.messages.append(sMessage)
        message['role'] = 'user'
        message['content'] = prompt
        self.messages.append(message)
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=self.messages,
                temperature=temp,
                stream=True
            )
        # the caller should call append_history
        except Exception as e:
            st.error(f'Error Occured : {e} ', icon="🚨")
            st.stop()
        return stream
    
    def getModelList(self) -> List[str] | bool:
        retList = []
        is_Connected = False
        try:
            model_list = self.client.models.list()
            for model in model_list.data:
                retList.append(model.id)
            is_Connected = True
        except Exception as e:
            print(f'Error Occured : {e} ')
        return retList, is_Connected


if __name__ == '__main__':
    client = OllamaClient(server='192.168.0.14')
    print(f'List of models are {client.getModelList()}')
    #while True:
    #    print('You :')
    #    response = client.chat_stream(model='dolphin-mistral:latest', temp=0.8, prompt=input())
    #    contents = ""
    #    AiMessage = {}
    #    for chunk in response:
    #        if chunk.choices[0].delta.content:
    #            content = chunk.choices[0].delta.content
    #            print(content, end='', flush=True)
    #            contents += content
    #    AiMessage['role'] = 'assistant'
    #    AiMessage['content'] = contents
    #    client.append_history(AiMessage)