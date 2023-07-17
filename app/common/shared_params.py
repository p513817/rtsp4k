import os

""" Define PARAMS Parameters """
class PARAMS:

    # For Swagger
    ROOT = "/rtsp4k"

    # For Service
    HOST = "0.0.0.0"
    PORT = os.environ["PORT"]
    CONF_PATH = "./config.json"
    API_VERSION = "/v1"
    
    # Basic Folder Path
    DATA_FOLDER = "./data"
    
    # Store Configuration Content
    CONF = None

    # Store Manager Object
    MAN = None
