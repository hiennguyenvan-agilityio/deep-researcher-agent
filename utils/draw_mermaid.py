from agents.deep_researcher.main import deep_researcher
from dotenv import load_dotenv

load_dotenv()

mermaid_code = deep_researcher.get_graph().draw_mermaid()

print(mermaid_code)
