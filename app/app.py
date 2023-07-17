# Basic
import os
import shutil
import logging

# About FastAPI
import uvicorn
from fastapi import FastAPI, WebSocket, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from typing import List, Optional, Literal
from pydantic import BaseModel

# Custom
from .common import RtspWrapper, PARAMS, Manager, read_config, init_logger, exception_message

# Init Logger
init_logger()

# Start up
app = FastAPI()

# If you need to use nginx, you have to add root
# app = FastAPI( root_path = PARAMS.ROOT )

# Resigter Router
# API_VERSION = '/v1'
# for router in routers:
#     app.include_router( router, prefix=API_VERSION )


# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    PARAMS.CONF = read_config(PARAMS.CONF_PATH)
    PARAMS.MAN = Manager()
    for route, info in PARAMS.CONF['streams'].items():        
        input = info["input"]
        try:
            PARAMS.MAN.add_stream(input, route)
        except Exception as e:
            logging.warning(f'Add stream ( {route}: {input}) failed.')
        PARAMS.MAN.print_console()

@app.on_event("shutdown")
def shutdown_event():
    try:
        PARAMS.MAN.release()
    except:
        pass
    logging.warning("Closed")

# --------------------------------------------------------------------

class Del_Data(BaseModel):
    route: str

# --------------------------------------------------------------------

@app.get("/", tags=["rtsp4k"])
async def root():
    return { "message": "hello kids, we can generate rtsp stream in simple way."}

@app.get("/streams", tags=["rtsp4k"])
async def get_streams():
    return { "message": PARAMS.MAN.get_all() } 


@app.post("/streams", tags=["rtsp4k"])
async def add_new_source(
    route: str,
    file: Optional[UploadFile] = File(None),
    input: Optional[str]= Form(None) ):
    """ Add new source
    ---

    """

    """
        - Expected Format: 
        `{
            "file": < Image | Video | Images > ,
            "input": < RTSP | V4L2 >,
            "route": str
        }`
    """
    # Helper function
    def save_file(file, path):
        """ Save file from fastapi """
        with open(file.filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        shutil.move(file.filename, path)

    # Got RTSP, V4L2
    if (file is None) or not (file.filename):
        name = input

    # Got file    
    else:

        # Single File
        path = os.path.join(PARAMS.DATA_FOLDER, file.filename)
        save_file(file=file, path=path)
        name = file.filename
        input = path

    try:
        # PARAMS.MAN.add_stream()
        data = PARAMS.MAN.add_stream(input=input, route=route)
        PARAMS.MAN.print_console()
        
        return { "message": data  }

    except Exception as e:
        raise HTTPException(status_code=500, detail=exception_message(e))

@app.delete("/streams", tags=["rtsp4k"])
async def del_stream(items: Del_Data):
    try:
        data = PARAMS.MAN.delete_stream(route=items.route)
        PARAMS.MAN.print_console()

        return { "message": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=exception_message(e))
