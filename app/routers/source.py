
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import Response

from typing import List, Optional, Literal
from pydantic import BaseModel

# Router
source_router = APIRouter(tags=["source"])

@source_router
def get_source_list():
    return 