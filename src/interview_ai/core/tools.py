import pandas, os, requests
from weasyprint import HTML
from .prompts import CSV_PROMPT, PDF_PROMPT, API_PROMPT
from .settings import settings
from .utilities import fetch_user_tools
from langchain_core.tools import StructuredTool
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.tools.bing_search import BingSearchResults
from langchain_community.utilities import BingSearchAPIWrapper


def generate_csv_file(data: dict) -> dict:
    root_dir = os.getcwd()
    csv_path = os.path.join(root_dir, "interview_ai", "interview_ai.csv")
    pandas.DataFrame(data).to_csv(csv_path, index=False)
    return {
        "label": "Download CSV File",
        "file_path":csv_path,
        "file_name":"interview_ai.csv",
        "mime":"text/csv"
    }

def generate_pdf_file(template: str) -> dict:
    root_dir = os.getcwd()
    pdf_path = os.path.join(root_dir, "interview_ai", "interview_ai.pdf")
    HTML(string = template).write_pdf(pdf_path)
    return {
        "label": "Download PDF File",
        "file_path":pdf_path,
        "file_name":"interview_ai.pdf",
        "mime":"application/pdf"
    }

def call_api_endpoint(api_details: dict) -> dict:
    try:
        response = requests.request(
            method = api_details["method"],
            url = api_details["endpoint"],
            headers = api_details["headers"],
            data = api_details["body"],
            files = [api_details["attachment"]]
        )
        return response.json()
    except:
        return {"error": "Failed to call API endpoint"}

# Tools
search_internet = BingSearchResults(api_wrapper=BingSearchAPIWrapper()) if (
    settings.internet_search == "bing"
) else DuckDuckGoSearchResults()
generate_csv_tool = StructuredTool.from_function(generate_csv_file, description = CSV_PROMPT)
generate_pdf_tool = StructuredTool.from_function(generate_pdf_file, description = PDF_PROMPT)
call_api_tool = StructuredTool.from_function(call_api_endpoint, description = API_PROMPT)
user_tools = fetch_user_tools()
