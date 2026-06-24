from agents.deep_researcher.main import deep_researcher_agent
from dotenv import load_dotenv

load_dotenv()

mermaid_code = deep_researcher_agent.get_graph().draw_mermaid()

print(mermaid_code)
