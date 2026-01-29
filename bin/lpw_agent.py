import streamlit as st
from lpw_init import *
from crewai import Agent, Task, Crew, LLM
import yaml
import os
import re

class LPWCrew:

    @staticmethod
    def _validate_server(server: str) -> None:
        """Validate server address to prevent SSRF attacks."""
        # Allow localhost, IP addresses, and domain names
        if not re.match(r'^(?:[a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+$|^localhost$|^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', server):
            raise ValueError(f"Invalid server address: {server}")

    @staticmethod
    def _validate_port(port) -> None:
        """Validate port number."""
        try:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                raise ValueError(f"Port must be between 1 and 65535: {port}")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid port number: {port}") from e
    def __init__(self, llm_host="127.0.0.1", llm_port="11434", model="llama3.1:latest"):
        # Validate inputs to prevent SSRF attacks
        self._validate_server(llm_host)
        self._validate_port(llm_port)

        self.llm_host = llm_host
        self.llm_port = llm_port
        self.model = model
        # Add 'openai/' prefix for litellm to recognize OpenAI-compatible endpoints
        # Only add prefix if no provider prefix exists (indicated by '/')
        litellm_model = f"openai/{model}" if "/" not in model else model
        self.llm = LLM(model=litellm_model, base_url=f'http://{llm_host}:{llm_port}/v1', api_key=os.getenv('OPENAI_API_KEY'))
        self.loadConfig()
        self.crew = Crew(
            agents = [self.sne_agent],
            tasks = [self.caTask]
        )
        print('#### Crew initialized')
    
    def kickoff(self, data, protocol) -> str:
        result = self.crew.kickoff(inputs={'pcap_data' : data, 'protocol' : protocol})
        return result.raw
    
    def loadConfig(self):
        agent_data = yaml.safe_load(returnValue('agent_config_file')) if returnValue('agent_config_file') else yaml.safe_load(returnValue('default_agent_config'))
        self.sne_agent = Agent(
            role = agent_data['role'],
            goal = agent_data['goal'],
            backstory=agent_data['backstory'],
            llm=self.llm,
            #verbose=True
        )
        print(f"##### {getLpwPath('temp')}/insights.md")
        self.caTask = Task(
            description=agent_data['tasks'][0]['description'],
            expected_output=agent_data['tasks'][0]['expected_output'],
            #output_file=f'{getLpwPath('temp')}/insights.md',
            agent=self.sne_agent
        )


if __name__ == '__main__':
    with open('temp/out.txt', 'r') as f:
        ac = LPWCrew()
        result = ac.kickoff(f.read(), 'ngap')
        print(f'Result : {result}')