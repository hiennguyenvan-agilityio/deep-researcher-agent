from agent import deep_researcher
from dotenv import load_dotenv
from IPython.display import display, Markdown

load_dotenv()

mermaid_code = deep_researcher.get_graph().draw_mermaid()

print(mermaid_code)