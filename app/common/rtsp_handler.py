#!/usr/bin/python3
import uuid
import os
import cv2
import time
import logging
import abc
import numpy as np
from typing import Tuple, Union, Literal, List

# Create Sourcer
import cicv
import threading

# Table
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich import box

# Custom
from .parser import write_config
from .shared_params import PARAMS

# Basic Wrapper
class Wrapper(abc.ABC):

    @property
    @abc.abstractclassmethod
    def show(self):
        raise NotImplementedError

    @property
    @abc.abstractclassmethod
    def release(self):
        raise NotImplementedError


class RtspWrapper(Wrapper):

    def __init__(self, 
                 width:int,
                 height:int,
                 fps:Union[int, float]=30,
                 name:Union[str, None]=None, 
                 server:str="localhost:8554" ):
        
        self.fps = int(fps)
        self.server = server
        
        # Gen Name
        if name is None:
            self.rtsp_name = str(uuid.uuid4())[:4]
        else:
            self.rtsp_name = name if name[0] != "/" else name[1:]

        # Get URL
        self.rtsp_url = f"rtsp://{self.server}/{self.rtsp_name}".replace(' ', '-')
        
        # Check Resize
        self.need_resize = False
        self.width, self.height = \
            self._get_size_h264((width, height))
        
        # Get Writter
        try:
            self.out = cv2.VideoWriter( 
                self.get_pipeline(), 
                cv2.CAP_GSTREAMER, 
                0, self.fps, (self.width, self.height), True )
        except Exception as e:
            raise RuntimeError("Initialize Video Writter ... Failed !!!")
        
        self._check_writter()

        # Set flag and fps
        self.is_ready = True
        self.display_fps = -1

    def show(self, frame:np.ndarray):
        t_start = time.time()
        self.is_ready = False
        self.out.write(self._resizer(frame))
        self.is_ready = True
        self.display_fps = 1//(time.time() - t_start)

    def get_pipeline(self):
        return self._def_pipeline()

    def get_url(self):
        return self.rtsp_url

    def release(self):
        self.out.release()

    def _check_writter(self):
        if not self.out.isOpened():
            raise Exception("Can not open video writer: {}".format(self.get_pipeline()))
        
    # def _cpu_pipeline(self):
    #     return \
    #         'appsrc is-live=true block=true format=GST_FORMAT_TIME ' + \
    #         f'caps=video/x-raw,format=BGR,width={self.width},height={self.height},framerate=30/1 ' + \
    #         ' ! videoconvert ! video/x-raw,format=I420 ' + \
    #         ' ! queue' + \
    #         ' ! x264enc bitrate=600 speed-preset=0 key-int-max=30' + \
    #         f' ! rtspclientsink location={self.rtsp_url}'

    def _def_pipeline(self):
        """
        speed-preset    : Preset name for speed/quality tradeoff options (can affect decode compatibility - impose restrictions separately for your target decoder)
        bitrate         : Bitrate in kbit/sec
        key-int-max     : Maximal distance between two key-frames (0 for automatic)
        """
        return 'appsrc ! videoconvert' + \
            ' ! x264enc speed-preset=ultrafast bitrate=600 key-int-max=' + str(self.fps*2 ) + \
            ' ! video/x-h264,profile=baseline' + \
            f' ! rtspclientsink location={self.rtsp_url}'

    def _resizer(self, frame:np.ndarray):
        """ A resizer to resize each frame """
        return cv2.resize( frame, (self.width, self.height) ) if self.need_resize else frame

    def _get_size_h264(self, org_size, limit_size=(3840, 2160)) -> Tuple[int, int]:
        """ Get closely quadruple value for width and height and set maxmium limit to 4K. 
        - Workflow
            1. Check the current resolution is less than limit resolution.
            2. Calculate quadruple size for h264 encode.
        - Args
            - org_size: a tuple with height and width. e.g. ( {width}, {height} )
        
        - Return
            - a new width and height  
        """

        max_h, max_w = limit_size[1], limit_size[0]     # Get Limit: 3840, 2160 -> (16 * 240 , 9 * 240)
        org_h, org_w = org_size[1], org_size[0]

        # Limit size
        if (org_h * org_w) > (max_h * max_w):
            self.need_resize = True
            print(
                f'The resolution is over the limitation, setup size to limitation ( H:{max_h},W:{max_w} )')
            return ( max_w, max_h )
        
        # Calculate quadruple ( 4*N )
        quadruple = lambda v: v if(v%4==0) else 4*((v//4)-1)            # helper function
        trg_w, trg_h = quadruple(org_w), quadruple(org_h)

        # Update resize flag
        if ((org_h, org_w) == (trg_h, trg_w) ):
            print('No need resize for h264')
        self.need_resize = True
        print('Need resize frame size to: {}x{} (W,H)'.format(trg_w, trg_h))
        
        return ( trg_w, trg_h )


class Displayer:

    def __init__(self, input:str, route:str, start_stream:bool=False) -> None:
        self.input = input
        self.route = route

        # Execute Flag
        self.is_stop = False

        # Main Object
        self.src = self._create_source()
        self.fps = self.src.get_fps()

        self.dpr = self._create_display()
        self.url = self.dpr.get_url()
        
        # Create threading
        self.worker = self._create_thread()

        # Start Thread if need
        if start_stream:
            self.worker.start()

    def _create_source(self):
        return cicv.Source( input = self.input, resolution=None )

    def _create_display(self):
        return RtspWrapper(name=self.route, width=self.src.width, height=self.src.height, fps=self.fps)

    def _create_thread(self):
        return threading.Thread( target=self._rtsp_thread, daemon=True )

    def _rtsp_thread(self):
        try:
            while(not self.is_stop):
                frame = self.src.read()
                self.dpr.show(frame)
        except Exception as e:
            logging.exception(e)
        finally:
            self.dpr.release()
            self.src.release()
            logging.warning(f'Displayer stopped ({self.route}: {self.url}) !!!')

    def get_url(self):
        return self.url

    def stop(self):
        self.is_stop = True
        if self.worker is not None and self.worker.is_alive():
            self.worker.join()
    
    def start(self):
        self.is_stop = False
        self.worker.start()


def _test_wait_loop():
    while(True):
        time.sleep(1)
        ans = input('Enter Q to leave: ')
        if ans.lower()=='q':
            break


def _test_displayer_func():
    dpr = Displayer(
        input='./data/funny_cat.mp4',
        route='sample',
        start_stream=True
    )

    _test_wait_loop()
    
    dpr.stop()        


# ----------------------------------------------------------------------


class ManagerWrapper(abc.ABC):

    @abc.abstractmethod
    def add_stream(self, input: str, route: str ): pass

    @abc.abstractmethod
    def delete_stream(self, uid:str): pass


class Manager(ManagerWrapper):

    def __init__(self) -> None:
        super().__init__()

        # Store each stream
        """
        {
            "route": {
                "input": str,
                "status": bool,
                "url": str            
            }, ...
        }
        """
        self.dprs = dict()
        self.info = dict()

    def _update_info(self, input:str, route:str, url:str, status:bool):
        self.info[route] = {
            "input": input,
            "status": status,
            "url": url
        }

    def _modifty_config(self):
        pass

    def add_stream(self, input: str, route: str ):
        # Check uid
        assert route not in self.dprs, "Duplicate name"
        success = True        
        try:
            
            # Generate RTSP
            self.dprs[route] = Displayer(
                input=input,
                route=str(route),
                start_stream=True
            )

            # NOTE: modify config
            if not route in PARAMS.CONF["streams"] :
                PARAMS.CONF["streams"][route] = {
                    "input": input
                }
                write_config(PARAMS.CONF_PATH, PARAMS.CONF)

        except Exception as e:
            logging.exception(e)
            success = False

        finally:
            self._update_info(
                input=input, 
                route=route, 
                url=self.dprs[route].get_url() if success else "", 
                status=success )
        
        return self.info[route]

    def delete_stream(self, route: str):
        try:
            input = self.dprs[route].input
            self.dprs[route].stop()
            del self.dprs[route]
            self.dprs.pop(route, None)
        
            # NOTE: Delete file
            PARAMS.CONF["streams"].pop(route, None)
            write_config(PARAMS.CONF_PATH, PARAMS.CONF)
            
            os.remove(input)
            
        except Exception as e:
            logging.exception(e)
            raise RuntimeError(f'Delete stream ({route}) .. failed !')
        
        finally:
            self.info.pop(route, None)

        return self.info
    
    def get_all(self) -> dict:
        return self.info
    
    def _rich_cell_styler(self, message:str, color: str) -> str:
        return f"[{color}]{message}[/{color}]"

    def _generate_table(self):
        table = Table(
            title="RTSP4K", 
            caption="Press Ctrl+C to leave ...", 
            box=box.ASCII)
        table.add_column("Status", justify="center", no_wrap=True)
        table.add_column("Route", justify="center", no_wrap=True)
        table.add_column("URL", style="magenta")
        table.add_column("Source")
        for route, info in self.info.items():
            s_content = "PASS" if info.get("status") else "FAIL"
            s_color = "green" if info.get("status") else "red"
            status = self._rich_cell_styler(s_content, s_color)
            table.add_row(status, route, info.get('url'), info.get("input"))
        return table

    def _clear_console(self):
        # os.system('cls' if os.name=='nt' else 'clear')
        print('\n')

    def print_console(self):
        self._clear_console()
        console = Console()
        console.print(self._generate_table())

    def live_console(self):
        try:
            self._clear_console()
            
            with Live(self._generate_table(), refresh_per_second=4) as live:
                while(True):
                    time.sleep(0.4)
                    live.update(self._generate_table())
        
        except KeyboardInterrupt:
            pass
        
        finally:
            for dpr in self.dprs.values():
                dpr.stop()

    def release(self):
        for dpr in self.dprs.values():
            dpr.stop()


def _test_manager():

    manager = Manager()

    manager.add_stream('./data/cat.jpg', 'cat')

    manager.live_console()


def _test_managet_with_config():

    from .shared_params import PARAMS
    from .parser import read_config

    manager = Manager()

    conf = read_config(PARAMS.CONF_PATH)

    for stream in conf['streams']:        
        route, input = stream['route'], stream["input"]
        try:
            manager.add_stream(input, route)
        except Exception as e:
            print(f'Add stream ( {route}: {input}) failed.')

    manager.live_console()


if __name__ == "__main__":
    """
    python3 -m app.common.rtsp_handler

    """
    _test_displayer_func()
    # _test_manager()
    # _test_managet_with_config()