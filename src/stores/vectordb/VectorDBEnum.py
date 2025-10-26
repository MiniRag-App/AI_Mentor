from enum import Enum

class VectorDBEnum(Enum):
    QDRANT ='QDRANT'
    PGVECTOR ='PGVECTOR'


class DistanceMethodEnum(Enum):
    COSINE ='cosine'
    DOT ='dot'

class  PGvectorTableSchemaEnums(Enum):
    ID = 'id'
    TEXT ='text'
    VECTOR ='vector'
    CHUNK_ID ='chunk_id'
    METADATA='metadata'
    _PREFIX ='pgvector'

class PGvectorDistanceMethodsEnum(Enum):
    COSINE ='vector_cosine_ops'
    DOT ='vector_l2_ops'

class PGVectorIndexTypeEnum(Enum):
    HNSW='hnsw'
    IVFFLAT = "ivfflat"
