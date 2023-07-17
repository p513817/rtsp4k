import json
import sys, traceback, logging
from typing import Union, Tuple

def parse_exception(error:Union[Exception, None]=None) -> tuple:
    """Parse Exception

    Args:
        error (Union[Exception, None], optional): the exception need parse. Defaults to None.

    Returns:
        tuple: _description_
    """

    if error is None:
        return (None, None, None, None, None)
    
    # Get Error Class ( type ) and Detail
    err_type    = error.__class__.__name__ 
    err_detail  = error.args[0] 

    # Last Data of Call Stack
    # Parse Call Stack and Combine Error Message
    cl, exc, tb = sys.exc_info()
    last_call_stack = traceback.extract_tb(tb)[-1] 
    file_name = last_call_stack[0] 
    line_num = last_call_stack[1] 
    func_name = last_call_stack[2] 

    return (err_type, err_detail, file_name, func_name, line_num)

def exception_message(error:Union[Exception, None]=None) -> str:
    e_type, e_detail, e_file, e_func, e_line = parse_exception(error=error)
    return f"{e_type}: {e_detail}"
    

"""Parse config for rtsp4k"""
def read_config(config_path:str) -> dict:
    with open(config_path, 'r') as f:
        data = json.load(f)
    return data

def write_config(config_path:str, json_data:dict) -> dict:
    # 
    with open(config_path, 'w') as f:
        json.dump(json_data, f)


if __name__ == "__main__":
    print(read_config('/workspace/config.json'))