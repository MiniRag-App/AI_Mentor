from enum import Enum

class ResponseSignals(Enum):
    
    FILE_TYPE_NOT_SUPPORTED ="file_type_not_supported"
    FILE_SIZE_EXEEDED ="file_size_exeeded"
    FILE_UPLOADED_SUCCESS="file_upload_successfully"
    FILE_UPLOADED_FAIL="file_uploaded_failed"
    FILE_VALIDATED_SUCESS ="file_validated_successfully"
    FILE_PROCESSING_SUCESS ='file processing success'
    FILE_PROCESSING_FIALED ='file processing faild'