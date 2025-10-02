import os 

class TemplateParser:

    def __init__(self,language:str=None,default_language:str ='en'):

        self.current_dir =os.path.dirname(os.path.abspath(__file__))
        self.default_language= default_language
        self.language =None

        self.set_language(language)


    def set_language(self, language:str):  # to be able to change language during run time

        if not language:
            self.language =self.default_language
        
        language_path =os.path.join(self.current_dir,"locales",language)

        if  os.path.exists(language_path):
            self.language =language

        else:
            self.language =self.default_language

    def get_prompt_value(self,group:str,key:str,vars:dict={}):
            # group --> file name
            # key ---> prompt name
            # vars ---> variable inside any template

            if not group or not key :
                 return None
            
            group_path =os.path.join(self.current_dir ,"locales",self.language,f"{group}.py")
            targeted_language =self.language

            if not os.path.exists(group_path):
                 # we will change group path into default language
                group_path =os.path.join(self.current_dir ,"locales",self.default_language,f"{group}.py")
                targeted_language =self.default_language
            
            if not os.path.exists(group_path):
                 return None
            
            # import group module
            module =__import__(f"stores.llm.templates.locales.{targeted_language}.{group}",fromlist=[group])
            
            
            if not module : # check if module is empty 
                 return None
            

            # get key attribute or prompt_name 
            key_attribute =getattr(module,key)

            return key_attribute.substitute(vars)
                 


