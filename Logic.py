from PyQt5 import QtWidgets, uic, QtWebEngineCore
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QUrl
from PyQt5 import QtWebEngineWidgets
import psutil
import pandas as pd
from PandasModel import PandasModel
from geolite2 import geolite2
import plotly.graph_objects as go
import socket
import geocoder
from os import path
import sys,time

destinations = []
reader = geolite2.reader()

class NetConMap(QtWidgets.QWidget):

    def __init__(self):
        super(NetConMap, self).__init__()
        self.loadUserInterface()

    def loadUserInterface(self):
        if getattr(sys, 'frozen', False):
            RELATIVE_PATH = path.dirname(sys.executable)
        else:
            RELATIVE_PATH = path.dirname(__file__)
        self._ui_path = RELATIVE_PATH  # Update this as needed
        uic.loadUi(path.join(self._ui_path, 'MainGui.ui'), self)
        self.setWindowTitle("NetConMap v1.1")
        first_processes = get_processes_info()
        self.ProcessInfo(first_processes)

        self.thread_process = QThread()
        self.worker_processes = Worker_processes()
        self.worker_processes.moveToThread(self.thread_process)
        self.thread_process.started.connect(self.worker_processes.run)
        self.worker_processes.processes_done.connect(self.ProcessInfo)
        self.thread_process.start()

        self.thread_map = QThread()
        self.worker_map = Worker_map()
        self.worker_map.moveToThread(self.thread_map)
        self.thread_map.started.connect(self.worker_map.run)
        self.worker_map.map_done.connect(self.MapView)
        self.thread_map.start()
        #self.pushButtonProcess.clicked.connect(lambda: ProcessInfo(self))
        #self.pushButtonMap.clicked.connect(lambda: MapView(self))

    def ProcessInfo(self,processes):
        df = construct_dataframe(processes)
        model = PandasModel(df)
        self.tableViewProcess.setModel(model)
    
    def MapView(self,map_url):
        self.widgetMap.load(map_url)

    def closeEvent(self, event):
        if self.isVisible():
            answer = QtWidgets.QMessageBox.question(
                self,
                'Are you sure you want to quit ?',
                'Task is in progress !',
                QtWidgets.QMessageBox.Yes,
                QtWidgets.QMessageBox.No)
            if answer == QtWidgets.QMessageBox.Yes:
                self.thread_process.quit()
                self.thread_process.deleteLater()
                self.worker_processes.deleteLater()
                self.thread_map.quit()
                self.thread_map.deleteLater()
                self.worker_map.deleteLater()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


class Worker_processes(QObject):
    processes_done = pyqtSignal(list)
    def __init__(self):
        super(Worker_processes, self).__init__()
    def run(self):
        """Long-running task."""
        while True:
            time.sleep(1)
            print('processes')
            processes = get_processes_info()
            self.processes_done.emit(processes)

class Worker_map(QObject):
    map_done = pyqtSignal(QUrl)
    def __init__(self):
        super(Worker_map, self).__init__()
    def run(self):
        """Long-running task."""
        while True:
            time.sleep(5)
            print('map')
            map_url = get_map()
            self.map_done.emit(map_url)

def get_size(bytes):
    """
    Returns size of bytes in a nice format
    """
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if bytes < 1024:
            return f"{bytes:.2f}{unit}B"
        bytes /= 1024

def get_processes_info(): # the list the contain all process dictionaries]
    processes = []
    for process in psutil.process_iter(): # get all process info in one shot
        with process.oneshot():

            pid = process.pid # get the process id
            if pid == 0: # System Idle Process for Windows NT, useless to see anyways                
                continue

            name = process.name() # get the name of the file executed
            try:
                memory_usage = process.memory_full_info().uss # get the memory usage in bytes
            except psutil.AccessDenied:
                memory_usage = 0

            try:
                cores = len(process.cpu_affinity()) # get the number of CPU cores that can execute this process
            except psutil.AccessDenied:
                cores = 0
            #cpu_usage = process.cpu_percent() # get the CPU usage percentage

            status = process.status() # get the status of the process (running, idle, etc.)

            try:
                username = process.username()  # get the username of user spawned the process
            except psutil.AccessDenied:
                username = "N/A"
            global destinations        
            for conn in process.connections():

                if status == 'running' and conn.status == 'ESTABLISHED' :
                    remote_ip = conn.raddr.ip
                    match = reader.get(remote_ip)
                    #if(match is not None):   #don't use because too many request error and slow to response
                        #R_lat = match['location']['latitude']
                        #R_lon = match['location']['longitude']
                    #match = geocoder.ip(conn.raddr.ip)
                    #match_me = geocoder.ip('me')  
                    if match is not None and conn.raddr.ip != '127.0.0.1':
                        R_lat = match['location']['latitude']
                        R_lon = match['location']['longitude']                        
                        destinations.append({'name':name,'lat':R_lat,'lon':R_lon,'pid':pid,'Remote':conn.raddr.ip})
                    elif remote_ip == '127.0.0.1':
                        R_lat = ""
                        R_lon = ""
                        remote_ip = "LOCALHOST"
                    else:                              
                        R_lat = ""
                        R_lon = ""
                        remote_ip = ""

                    processes.append({'pid': pid, 'name': name, 'cores': cores, 'memory_usage': memory_usage, 'username': username,'Local port':conn.laddr.port, 'Remote IP':remote_ip, 'Remote Port':conn.raddr.port, 'Latitude':R_lat, 'Longitude':R_lon, })

    return processes

def get_Host_name_IP(remote_ip): 
    try: 
        host_name = socket.gethostbyaddr(remote_ip) 
    except: 
        host_name = (remote_ip,"","")
    return host_name

def construct_dataframe(processes): 
    df = pd.DataFrame(processes) # convert to pandas dataframe  
    df.set_index('pid', inplace=True) # set the process id as index of a process  
    df.sort_values('pid', inplace=True, ascending=True) # sort rows by the column passed as argument   
    df['memory_usage'] = df['memory_usage'].apply(get_size) # pretty printing bytes   
    #df = df[columns.split(",")] # reorder and define used columns
    return df

def get_map():
    match_myip = geocoder.ip('me')

    if match_myip.ok:
        my_lat = match_myip.lat
        my_lon = match_myip.lng
        my_ip = match_myip.ip
    else:                                
        my_lat = '0'
        my_lon = '0'
        my_ip = "Not Found"

    fig = go.Figure(go.Scattergeo(mode = "markers+lines",name = "Me "+ my_ip,lon = [my_lon, my_lon],lat = [my_lat, my_lat],marker = {'size': 10}))

    for coor in destinations:
        remote = (coor['Remote'],"","")
        fig.add_trace(go.Scattergeo(
            mode = "markers+lines",
            name = coor['name']+" "+remote[0],
            lon = [my_lon, coor['lon'] ],
            lat = [my_lat, coor['lat']],
            marker = {'size': 10}))

    fig.update_geos(fitbounds="locations")
    fig.update_layout(
        margin ={'l':0,'t':0,'b':0,'r':0},
        height=600,
        width=1400,
        mapbox = {'center': {'lon': my_lon, 'lat': my_lat},'style': "stamen-terrain"}
        )
    fig.write_html('first_figure.html')

    file_path = path.abspath(path.join(path.dirname(__file__), "first_figure.html"))
    local_url = QUrl.fromLocalFile(file_path)
    return local_url
