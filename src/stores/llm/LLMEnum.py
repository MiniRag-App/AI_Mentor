from enum import Enum 

class LLMEnum(Enum):
    OPENAI ='OPENAI'
    COHER='COHER'
    GROQ='GROQ'
    OPENROUTER='OPENROUTER'


class OpenAIEnum(Enum):
    SYSTEM ='system'
    USER ='user'
    ASSISTANT ='assistant'

class CoherEnum(Enum):
    SYSTEM ='system'
    USER ='user'
    ASSISTANT ='assistant'
    DOCUMENT= 'search_document'
    QUERY= 'search_query'

class DocumentTypeEnum(Enum):
    DOCUMENT= 'document'
    QUERY= 'query' 