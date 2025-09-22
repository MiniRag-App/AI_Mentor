from enum import Enum

class ResponseSignals(Enum):
    
    FILE_TYPE_NOT_SUPPORTED ="file_type_not_supported"
    FILE_SIZE_EXEEDED ="file_size_exeeded"
    FILE_UPLOADED_SUCCESS="file_upload_successfully"
    FILE_UPLOADED_FAIL="file_uploaded_failed"
    FILE_VALIDATED_SUCESS ="file_validated_successfully"
    FILE_PROCESSING_SUCESS ='file processing success'
    FILE_PROCESSING_FIALED ='file processing faild'
    NO_FILES_ERROR='not found files'
    FILE_ID_ERROR='no file_id found with this id'
    PROJEFT_NOT_FOUND='project not found'
    INSERT_INOT_VECTOR_DB_ERROR ='Insert into vectordb error'
    INSERT_INTO_VECTORDB_SUCCESS='Insert into vectordb success'
    NOT_EXISTED_CHUNKS_FOR__PROJET_ID ='not existed chunks for project id'
    NO_FOUND_INFO_ABOUT_PROJECT_IN_VECTORDB ='no found info about project in vectordb'
    VECTORDB_COLLECTION_INFO_RETRIVED= 'vectordb collection info retrived'
    VECTOREDB_SEARCH_ERROR ="vectordb_search_error"
    VECTORDB_SEARCH_SUCCESS ="vectordb_search_success"