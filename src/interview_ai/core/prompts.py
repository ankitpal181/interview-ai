from datetime import datetime

CSV_PROMPT = """
    Generates a structured CSV file from conversational data points provided in a dictionary format.

    **Purpose:** This tool should be used when the user explicitly requests to **export, compile, or
    generate structured analytical data** from the conversation into a file for analysis or import
    (i.e., a CSV file).

    ## Instructions for LLM Preparation

    The LLM must perform the following critical steps before calling this tool:

    1.  **Data Extraction & Synthesis:** Review the conversation history to identify and extract all
        relevant data, metrics, or comparative points that need to be structured into a table/spreadsheet
        format.
    2.  **Structuring into Dictionary Format (Crucial):**
        a. The data must be compiled into a **Python dictionary**.
        b. The dictionary keys **must** represent the **column names** (headers) of the final CSV file
        (e.g., 'Project Name', 'Status', 'Completion Date', 'Metric Value').
        c. The dictionary values **must** be **lists** (or arrays) where each list contains the
        corresponding data points for that column, ensuring that all lists are of **equal length** to
        form coherent rows.

        > **Example Dictionary Structure:**
        > `{'Topic': ['Apples', 'Bananas', 'Oranges'], 'Price': [1.0, 0.5, 1.25],
        'Quantity': [100, 250, 75]}`

    3.  **Data Quality:** Ensure the extracted data points are clean, consistent, and ready for
        analytical use.

    ## Arguments

    :param data: The well-structured Python dictionary where keys are CSV headers and values are
    equal-length lists of data points, ready for conversion.
    :type data: dict

    ## Returns

    :returns: A dictionary confirming the successful creation of the CSV file and containing summary
    metadata or the file path.
    :rtype: dict
"""
PDF_PROMPT = """
    Creates a professional, formatted PDF document based on structured data provided as an HTML template.

    **Purpose:** This tool should be used when the user explicitly requests to **generate, create, or
    export a PDF report, document, or file** containing summarized or structured information discussed
    in the conversation.

    ## Instructions for LLM Preparation

    The LLM must perform the following steps before calling this tool:

    1.  **Content Selection:** Review all relevant conversation history to extract and synthesize the
        core data and information intended for the PDF.
    2.  **Dynamic Template Generation (HTML):**
        a. **Analyze the Content Type:** Determine the nature of the data (e.g., meeting summary,
        financial report, project plan, research analysis, etc.).
        b. **Create a Professional HTML Template:** Generate a complete, self-contained HTML string that
        serves as the PDF template. This template **must** be professionally designed (using appropriate
        CSS inline or `<style>` blocks) to ensure high-quality presentation, clear hierarchy, design, and
        readability.
        c. **Mandatory Inclusion:** The HTML must include a professional title, the date of creation, and
        logical structural elements (headings, paragraphs, lists) for the included data.
    3.  **Data Visualization (Crucial):**
        a. If the data contains **quantitative, numerical, or comparative information** (e.g., statistics,
        trends, metrics), the generated HTML **MUST** include embedded code (e.g., a JavaScript library
        like Chart.js or an image URL) to render relevant **graphs, charts, or histograms** to visualize
        the data effectively.

    ## Arguments

    :param template: The complete, professional, and dynamically generated HTML string that will
    serve as the PDF's content and template.
    :type template: str

    ## Returns

    :returns: A dictionary confirming the successful creation of the CSV file and containing summary
    metadata or the file path.
    :rtype: dict
"""
INTERVIEWBOT_PROMPT = """
    ## Interview Simulation System Prompt

    ### **Role and Goal**

    You are a **Specialized Interviewer AI** designed to simulate a professional interview for a **{role}** role.
    Your primary goal is to assess the candidate's knowledge depth, problem-solving skills, communication clarity,
    and overall fit for the job position.

    ### **Interview Procedure and Constraints**

    1.  **Preparation (Mandatory):**
        * **Input:** The user will provide their name, the role for which the interview is being simulated, along with
        a list of preferred companies (if any) and a time frame for each question.
        * **Action:** Conduct a search, using search tools provided, for the **latest, industry-relevant topics,
        concepts, and challenging questions** appropriate for the {role} role in related domains. Also consider the type
        of questions asked by preferred companies, such as [{companies}], if given in the list. Each question must be of
        nature that can be answered in {time_frame} minutes. Only ask {questions_type} questions.
        * **Output:** Prepare a comprehensive list of {no_of_questions} of these questions and mention the
        type({questions_type}) and companies that usually ask this type of question for each question.

    2.  **Post-Interview Analysis (Final Stage):**
        * **Input:** The user will provide a key value pair of question and answer in a list/dict format.
        * **Evaluation:** Conduct a detailed, multi-faceted analysis of the provided answers:
            * **Rating:** Assign a rating to each individual answer: **Good**, **Average**, or **Bad**.
            * **Feedback:** For *every* answer, provide detailed, actionable feedback. Explain **in detail what went
            wrong** (technical/knowledge inaccuracy, lack of depth, poor structure) and **how the answer could have
            been improved** (specific concepts to mention, better approach, clearer explanation).
            * **Performance Metrics:** Judge the candidate's performance across the entire interview on the following
            criteria:
                * **Confidence:** Assess the level of certainty and clarity in the presentation.
                * **Answering Patterns:** Note any recurring positive or negative habits (e.g., rambling, jumping to
                conclusions, excellent structuring).
                * **Clarity & Completeness within Time:** Judge whether the candidate was able to **clearly and
                completely explain** the solution/concept within the strict 10-minute timeframe.

    ### **Final Verdict**

    Conclude the entire interaction with a **clear, unambiguous verdict** on the candidate's capability for the
    {role} role. If the verdict is negative ("Not Capable"), you must provide a concise, prioritized list of
    **key reasons why** (e.g., "Lacks deep knowledge in Distributed Transactions," "System design lacked metrics and
    failure analysis.").
"""
REPORTING_PROMPT_MAP = {
    "pdf": """ - Generate a PDF report of the conversion and evaluation of the interview.
    Keep the evaluation intact and don't try to summarise it.
    Use pdf part of the response schema for this part's response.""",
    "email": """ - Generate email subject and body to inform the receiver about the interview
    for each email request by user. If user provides a template, use it for the body.
    Use email part of the response schema for this part's response.""",
    "whatsapp": """ - Generate whatsapp message to inform the receiver about the interview
    for each whatsapp request by user. If user provides a template, use it for the message.
    Use whatsapp part of the response schema for this part's response.""",
    "description_value": """ - Generate value using given description, key name and interview data
    for each description_value request by user. 
    Use description_value part of the response schema for this part's response."""
}
REPORTING_PROMPT = """
    You are an AI post interview analyst. Your job is to generate different information pieces based on the given
    instructions below:
    
    {pdf}
    {email}
    {whatsapp}
    {description_value}

    Read user messages to get context of the conversation and data to be used for information generation.
"""
API_PROMPT = """
    Executes an HTTP request to a specified API endpoint with customizable method, headers, body, and attachments.

    **Purpose:** This tool should be used when there is a need to **trigger external webhooks, send data to 
    third-party services, or integrate with external APIs** as part of the reporting or post-interview workflow.

    ## Instructions for LLM Preparation

    The LLM must perform the following steps before calling this tool:

    1.  **Endpoint Identification:** Determine the target URL (endpoint) where the request should be sent.
    2.  **Method Selection:** Choose the appropriate HTTP method (e.g., 'POST', 'PUT', 'GET', 'PATCH') based 
        on the API's requirements and the action being performed.
    3.  **Header Configuration:** Construct a dictionary of necessary HTTP headers (e.g., 
        `{"Content-Type": "application/json", "Authorization": "Bearer ..."}`).
    4.  **Body Preparation:** Synthesize and format the data to be sent in the request body. If the API 
        expects JSON, ensure the body is structured accordingly.
    5.  **Attachment Handling:** If a file (such as an evaluation PDF or CSV) needs to be uploaded, 
        provide the absolute file path as the 'attachment'.

    ## Arguments

    :param api_details: A dictionary containing the full configuration for the API call.
        - 'method' (str): The HTTP method to use (e.g., "POST").
        - 'endpoint' (str): The destination URL.
        - 'headers' (dict): A key-value pair of HTTP headers.
        - 'body' (dict/str): The payload/data to be sent in the request.
        - 'attachment' (str): The file path of any attachment to be included in the request.
    :type api_details: dict

    ## Returns

    :returns: A dictionary containing the JSON response from the API or an error message if the call fails.
    :rtype: dict
"""
