from enum import Enum 

class LLMEnum(Enum):
    OPENAI ='OPENAI'
    COHER='COHER'
    GROQ='GROQ'
    OPENROUTER='OPENROUTER'


class GroqEnum(Enum):
    SYSTEM ='system'
    USER ='user'
    ASSISTANT ='assistant'