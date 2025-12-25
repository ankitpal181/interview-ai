import pandas
from weasyprint import HTML
from .prompts import CSV_PROMPT, PDF_PROMPT
from .settings import settings
from .utilities import fetch_user_tools
from langchain_core.tools import StructuredTool
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.tools.bing_search import BingSearchResults
from langchain_community.utilities import BingSearchAPIWrapper


def generate_csv_file(data: dict) -> dict:
    pandas.DataFrame(data).to_csv('chatbot.csv', index=False)
    return {
        "label": "Download CSV File",
        "file_path":'chatbot.csv',
        "file_name":"data.csv",
        "mime":"text/csv"
    }

def generate_pdf_file(template: str) -> dict:
    HTML(string = template).write_pdf("chatbot.pdf")
    return {
        "label": "Download PDF File",
        "file_path":'chatbot.pdf',
        "file_name":"data.pdf",
        "mime":"application/pdf"
    }

# Tools
search_internet = BingSearchResults(api_wrapper=BingSearchAPIWrapper()) if (
    settings.internet_search == "bing"
) else DuckDuckGoSearchResults()
generate_csv_tool = StructuredTool.from_function(generate_csv_file, description = CSV_PROMPT)
generate_pdf_tool = StructuredTool.from_function(generate_pdf_file, description = PDF_PROMPT)
user_tools = fetch_user_tools()
