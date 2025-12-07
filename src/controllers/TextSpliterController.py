from logging import Logger
from .BaseController import BaseController
from typing import Dict
import re
from models.db_schemes.mini_rag.schemes import DataChunk
from models.enumrations.QueryEnum import QueryEnum

class TextSpliterController(BaseController):
    def __init__(self,doc_type:str):
        super().__init__()
        # Common CV section headers (regex patterns)
        self.cv_section_pattern = {
            'summary': r'(professional\s+summary|summary|profile|objective|about\s+me)',
            'experience': r'^(work\s+experience|professional\s+experience|employment\s+history|experience)$',
            'education': r'(education|academic\s+background|qualifications)',
            'skills': r'(skills|technical\s+skills|core\s+competencies|expertise)',
            'projects': r'(projects|key\s+projects|notable\s+projects)',
            'certifications': r'(certifications|certificates|licenses)',
            'achievements': r'(achievements|awards|accomplishments)',
            'languages': r'(languages|language\s+proficiency)',
            'contact': r'(contact|personal\s+information|details)'
        }
        
        self.JD_section_pattern = {
        'summary': r'^(job\s+summary|about\s+the\s+job|role\s+overview)$',
        'responsibilities': r'^(key\s+responsibilities|responsibilities|duties)$',
        'requirements': r'^(required\s+skills\s*&\s*qualifications|requirements|qualifications)$',
        'preferred': r'^(preferred\s+qualifications|preferred|nice\s+to\s+have)$',
        'company': r'^(about\s+us|company|who\s+we\s+are)$',
        }

        
        self.doc_type =doc_type
        self.section_pattern =self.cv_section_pattern if self.doc_type == QueryEnum.CV.value else self.JD_section_pattern
        
        self.logger =Logger("uvicorn")
        
    
    def identify_sections(self,text) -> Dict[str,str]:
        
        # step1: split texts into lines 
        lines =text.split('\n')
          # setp2: define sections 
        sections ={}
        
           
        # step3: define current section 
        current_section ='unknown'
        sections['unknown'] =[]
        # loop for each line and compare it with regex 
        for line in lines:
            lower_line =line.lower().strip()  
            
            # seach for regex in lin 
            section_found =False  
            
            for section_name ,pattern in self.section_pattern.items():
                # check if the line is a header
                if re.fullmatch(pattern,lower_line,re.IGNORECASE):
                    current_section = section_name
                    
                    sections.setdefault(current_section, [])
                    section_found =True
                    break
                    
            # add not header lines to current section 
            if not section_found and line.strip():
                sections[current_section].append(line)
                
        return {k: "\n".join(v).strip() for k, v in sections.items() if v}
    
    def split_text_chunks (self,text:str,project_id:int,asset_id:int):
        # step1: split cv into sections 
        sections =self.identify_sections(text =text)
        
        if len(sections) == 0 or not sections:
            return self.logger.info("number of chunks = 0")
        
        chunks =[
                DataChunk(
                    chunk_text=section_text,
                    chunk_metadata =[],
                    chunk_order= idx,
                    chunk_doc_type=self.doc_type,
                    chunk_project_id =project_id,
                    chunk_asset_id =asset_id
                )
                for idx ,(section_name ,section_text) in enumerate(sections.items())
            ]
        
        return chunks
            
          
        
            
            
            
                
                
        
        