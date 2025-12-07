import json
import json_repair
from openai import OpenAI
# import groq api from .env file 
from dotenv import load_dotenv
import os
from pydantic import BaseModel,Field
from typing import Literal, List
# load content from files using langchain 
from langchain_community.document_loaders import PyPDFLoader,TextLoader

load_dotenv()

print("Loaded key: ", os.getenv("Gemini_API_KEY"))
client = OpenAI(api_key=os.getenv("Gemini_API_KEY"),
         base_url="https://generativelanguage.googleapis.com/v1beta/openai/")





class Question(BaseModel):
    question: str =Field(..., description="The evaluation question to be asked")
    query_type: Literal["CV", "JOB", "BOTH"] =Field(..., description="Type of query: CV-only, JD-only, or Both")
    ground_truth: str =Field(..., description="the correct answer based strictly on CV/JD , complete answer with all details ")


class QuestionList(BaseModel):
    Questions: List[Question] =Field(..., description="List of evaluation questions")


def generate_test_questions(cv_text, jd_text):
    prompt = f"""
    Generate EXACTLY 20 evaluation questions for an AI Career Mentor RAG system.
    **Question Types (distribute evenly):**
    1. Strengths: "What are MY main strengths for this role?"
    2. Weaknesses/Gaps: "What skills am I missing?"
    3. Specific Skills: "How does my [X] experience align with requirements?"
    4. Guidance: "What roadmap should I follow to fill gaps?"
    5. Assessment: "Score my fit 0-100 with explanation"
    **Requirements:**
    - Questions from USER perspective (use "my", "I", "me") - act as the user asking about themselves
    - Reference specific skills/projects/requirements from documents
    - Mix of simple and complex questions
    - Cover CV-only, JD-only, and comparison scenarios
    Write answers as if you're a helpful career advisor having a friendly conversation. 
     DO:
    - Write in natural, conversational language
    - Use "you have", "your experience shows", "you're missing"
    - Combine related points in flowing paragraphs
    - Be direct and clear
    - For BOTH queries: naturally weave together CV evidence and JD requirements
     DON'T:
    - Use bullet points, asterisks, or formal structures (* ** - etc.)
    - Be overly formal or academic
    **Documents:**
    CV:
    \"\"\"{cv_text}\"\"\"

    Job Description:
    \"\"\"{jd_text}\"\"\"

    **Output Schema:**
    {json.dumps(QuestionList.model_json_schema(), ensure_ascii=False)}
    Output ONLY valid JSON matching the schema.
    """
    
    completion = client.chat.completions.create(
            model="gemini-2.5-pro",
            messages=[
            {
                "role": "user",
                "content": prompt
            }
            ],
            temperature=0,
        )

    output =completion.choices[0].message.content
    # response_text = completion.choices[0].message['content']
    # print("\nFull response text:", response_text)
    # questions_data = json.loads(output)
    print(output)
    return json_repair.loads(output)

# Usage
pdf_loader = PyPDFLoader("src/assets/files/5/063fmxw6gnr8_ShroukAdel_CV.pdf")
cv_docs = pdf_loader.load()
cv_text = "\n".join([doc.page_content for doc in cv_docs])
text_loader = TextLoader("src/assets/files/5/jbxf1uwx4zbo_AI_Job.txt", encoding='utf-8')
jd_docs = text_loader.load()
jd_text = "\n".join([doc.page_content for doc in jd_docs])

test_questions = generate_test_questions(cv_text, jd_text)

# Save to file
with open("src/evaluation/evaluation_dataset.json", "w") as f:
    json.dump(test_questions, f, indent=2)
    print("Saved evaluation_dataset.json successfully!")