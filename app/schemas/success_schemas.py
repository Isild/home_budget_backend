from pydantic import BaseModel

class SuccessResponseSchema(BaseModel):
    message: str
