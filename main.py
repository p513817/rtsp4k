#!/usr/bin/python3

# Just load app
import uvicorn
from app import app, PARAMS, read_config


if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host = PARAMS.HOST, 
        port = int(PARAMS.PORT),
        reload=True )