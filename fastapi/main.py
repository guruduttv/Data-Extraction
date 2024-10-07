import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import instructor
import anthropic
from fastapi.middleware.cors import CORSMiddleware
import json
from dotenv import load_dotenv
load_dotenv()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Defining the request body model
class UserField(BaseModel):
    name: str
    data_type: str
    description: str


class ExtractionRequest(BaseModel):
    document_text: str
    fields: List[UserField]

#Use of env file and to access the apikey
API_KEY = "Api-Key"

client = instructor.from_anthropic(anthropic.Anthropic(api_key=API_KEY))

# Token limit
MAX_TOKENS = 4096
MAX_PROMPT_TOKENS = 1500  # Estimation for prompt tokens usage
MAX_RESPONSE_TOKENS = MAX_TOKENS - MAX_PROMPT_TOKENS


#Function to split document into chunks so that api response wont be more than 4096 tokens
def split_text_into_chunks(text: str, max_chunk_size: int):
    words = text.split()
    chunks = []
    chunk = []

    for word in words:
        chunk.append(word)
        if len(' '.join(chunk)) > max_chunk_size:
            chunks.append(' '.join(chunk))
            chunk = []

    if chunk:
        chunks.append(' '.join(chunk))

    return chunks


# Function to call LLM API and get both extracted values and the text references based on the fields
def extract_data_with_reference(data: str, fields: List[Dict[str, str]]) -> Dict[str, dict]:
    field_descriptions = ", ".join(
        [f"{field.name} {field.data_type}  :  {field.description}" for field in fields]
    )

    try:
        response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=MAX_RESPONSE_TOKENS,
                response_model=None,
                system="Extract data based on user-defined fields only  and provide references from where exactly in the chunk the data was extracted.",
                messages=[{
                "role": "user",
                "content": f"""
                       You are tasked with extracting specific data from the chunk based on the following fields:

                       {field_descriptions}

                       Analyze the text below and extract relevant values. Return the output in the following JSON format:

                       {{
                           "extracted_values": [
                               {{
                                   "value": "{{extracted_value}}",
                                   "reference": "{{brief reference}}"
                               }},
                               ...
                           ]
                       }}

                       **Instructions:**
                       - Omit values like "N/A", "none" return an empty JSON object: {{}} as response. 
                       - If no valid values are found, return an empty JSON object: {{}} as response.
                       - Ensure the output is strictly valid JSON.

                       Chunk to extract from:
                       {data}
                """}]
        )


        # Return the response having both  the extracted values and the parts of the document they were extracted from
        return response.content[0].text if response.content else {}
    except Exception as e:
        return {"error": str(e)}


# Function to merge responses from multiple chunks
def merge_responses(responses: List[Dict[str, dict]]) -> Dict[str, List[Dict[str, str]]]:
    merged = {"extracted_values": []}

    for response in responses:
        if "extracted_values" in response:
            merged["extracted_values"].extend(response["extracted_values"])

    return merged

# Main function to get all data like document text and the fields
@app.post("/extract")
async def extract_fields(request: ExtractionRequest):
    document_text = request.document_text
    fields = request.fields
    # Breaking  the document into chunks
    chunks = split_text_into_chunks(document_text, max_chunk_size=MAX_RESPONSE_TOKENS)
    all_responses = []
    for chunk in chunks:
        # Call the LLM model for each chunk to extract data
        response = extract_data_with_reference(chunk, fields)
        if response :
            try:
                #Making sure the output is in json format
                json_output = json.loads(response)
                all_responses.append(json_output)
            except Exception as e:
                print(str(e))
                return {"error": str(e)}
    final_result = merge_responses(all_responses)
    return final_result
