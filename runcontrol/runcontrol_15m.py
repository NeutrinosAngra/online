#! /usr/bin/env python3
import socket
import time
import subprocess
import threading

import redis
import numpy as np
import pandas as pd
import struct
import time

from multiprocessing.dummy import Pool as ThreadPool 
pool = ThreadPool(4)

class RPiQueue:
    
    redisConn = None
    QUEUE_NAME = 'queueEvents'
    
    
    def __init__(self):
        pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
        self.redisConn = redis.Redis(connection_pool=pool)
        
    def read_one(self,memorypage):
        QUEUE_NAME = self.QUEUE_NAME + str(memorypage)
        try:
            k_data = self.redisConn.rpop(QUEUE_NAME)
            return k_data
        except:
            return None

    def clear_all(self,memorypage):
        QUEUE_NAME = self.QUEUE_NAME + str(memorypage)
        k_data = self.redisConn.rpop(QUEUE_NAME)
        i = 0
        while (k_data != None):
            #print(i)
            i+=1
            k_data = self.redisConn.rpop(QUEUE_NAME)
        print(str(i) + ' eventos apagados da fila '+ QUEUE_NAME)

def start_trigger():
    HOST='192.168.136.4'
    PORT=5000
    tcp=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    dest=(HOST,PORT)
    tcp.connect(dest)
    msg = 'R'
    tcp.send(str(msg).encode('ascii'))
    MSG_FROM_SERVER = tcp.recv(4096)
    #if MSG_FROM_SERVER:
    #    print(MSG_FROM_SERVER)
    tcp.close()

def stop_trigger():
    HOST='192.168.136.4'
    PORT=5000
    tcp=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    dest=(HOST,PORT)
    tcp.connect(dest)
    msg = str('Q')
    tcp.send(msg.encode('ascii'))
    MSG_FROM_SERVER = tcp.recv(4096)
    #if MSG_FROM_SERVER:
    #    print(MSG_FROM_SERVER)
    time.sleep(0.2)
    msg = str('I')
    tcp.send (msg.encode('ascii'))
    MSG_FROM_SERVER = tcp.recv(4096)
    #if MSG_FROM_SERVER:
    #    print(MSG_FROM_SERVER)
    time.sleep(0.2)
    msg = str('L')
    tcp.send (msg.encode('ascii'))
    MSG_FROM_SERVER = tcp.recv(4096)
    #if MSG_FROM_SERVER:
    #    print(MSG_FROM_SERVER)
    time.sleep(0.2)
    msg = str('P')
    tcp.send (msg.encode('ascii'))
    MSG_FROM_SERVER = tcp.recv(4096)
    #if MSG_FROM_SERVER:
    #    print(MSG_FROM_SERVER)
    time.sleep(0.2)
    tcp.close()
    
def start_daq(memorypage):
    if (memorypage == 1): 
        p = subprocess.Popen(['ssh', '192.168.136.3', '/home/lsd/angraNDAQ1_15m'])
    elif (memorypage == 2): 
        p = subprocess.Popen(['ssh', '192.168.136.3', '/home/lsd/angraNDAQ2_15m'])
    
def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val                         # return positive value as is

current_milli_time = lambda: int(round(time.time() * 1000))

def save_file(memorypage):
    global queue
    colunas = ['Event Number', 'Timestamp', 'NDAQ Number', 'Slot Number', 'Trigger Flags', 'BusyFlag' , 'FlashADC_1', 'FlashADC_2', 'FlashADC_3', 'FlashADC_4', 'FlashADC_5', 'FlashADC_6', 'FlashADC_7', 'FlashADC_8']
    df = pd.DataFrame(columns=colunas)
    df = df.astype('int32')
    step= 4
    ADC = 100
    local_var = 3
    headers = 12
    init_adc_point = 15
    num = 1
    temp_mcounter = []
    temp_timestamp = []
    temp_ndaq = []
    temp_slot = []
    temp_flags = []
    temp_busyflag = []
    temp_adc1 = []
    temp_adc2 = []
    temp_adc3 = []
    temp_adc4 = []
    temp_adc5 = []
    temp_adc6 = []
    temp_adc7 = []
    temp_adc8 = []

    while (True):
        raw = queue.read_one(memorypage) 
        if (raw == None): 
            break
        full_data = []
        for i in range(0,len(raw),step):
            d = raw[i:i+step]
            full_data.append(struct.unpack('>i', d)[0])
        for j in range(0,len(full_data),215):
            slot = int(full_data[0+j])
            ndaq = int(full_data[1+j])
            flags = int(full_data[2+j])
            mcounter = int(full_data[3+j])
            busyflag = int(full_data[4+j]>>31)
            timestamp = int(full_data[5+j])
            adc1 = []
            adc2 = []
            adc3 = []
            adc4 = []
            adc5 = []
            adc6 = []
            adc7 = []
            adc8 = []
            for i in range (0,int(ADC/2)):
                adc1.append(twos_comp(full_data[init_adc_point+i+j] & 0xFF,8))
                adc1.append(twos_comp(full_data[init_adc_point+i+j] >> 8  & 0xFF,8))
                adc2.append(twos_comp(full_data[init_adc_point+i+j] >> 16  & 0xFF,8))
                adc2.append(twos_comp(full_data[init_adc_point+i+j] >> 24  & 0xFF,8))
            for i in range (int(ADC/2),int(ADC)):
                adc3.append(twos_comp(full_data[init_adc_point+i+j] & 0xFF,8))
                adc3.append(twos_comp(full_data[init_adc_point+i+j] >> 8  & 0xFF,8))
                adc4.append(twos_comp(full_data[init_adc_point+i+j] >> 16  & 0xFF,8))
                adc4.append(twos_comp(full_data[init_adc_point+i+j] >> 24  & 0xFF,8))
            for i in range (int(ADC),int(3*ADC/2)):
                adc5.append(twos_comp(full_data[init_adc_point+i+j] & 0xFF,8))
                adc5.append(twos_comp(full_data[init_adc_point+i+j] >> 8  & 0xFF,8))
                adc6.append(twos_comp(full_data[init_adc_point+i+j] >> 16  & 0xFF,8))
                adc6.append(twos_comp(full_data[init_adc_point+i+j] >> 24  & 0xFF,8))
            for i in range (int(3*ADC/2),2*ADC):
                adc7.append(twos_comp(full_data[init_adc_point+i+j] & 0xFF,8))
                adc7.append(twos_comp(full_data[init_adc_point+i+j] >> 8  & 0xFF,8))
                adc8.append(twos_comp(full_data[init_adc_point+i+j] >> 16  & 0xFF,8))
                adc8.append(twos_comp(full_data[init_adc_point+i+j] >> 24  & 0xFF,8))
            temp_mcounter.append(mcounter)
            temp_timestamp.append(timestamp)
            temp_ndaq.append(ndaq)
            temp_slot.append(slot)
            temp_flags.append(flags)
            temp_busyflag.append(busyflag)
            temp_adc1.append(np.array(adc1))
            temp_adc2.append(np.array(adc2))
            temp_adc3.append(np.array(adc3))
            temp_adc4.append(np.array(adc4))
            temp_adc5.append(np.array(adc5))
            temp_adc6.append(np.array(adc6))
            temp_adc7.append(np.array(adc7))
            temp_adc8.append(np.array(adc8))
            num+=1
            if (num%1000 == 0):
                print(num)


    df['Event Number'] = temp_mcounter
    df['Timestamp'] = temp_timestamp
    df['NDAQ Number'] = temp_ndaq
    df['Slot Number'] = temp_slot
    df['Trigger Flags'] = temp_flags
    df['BusyFlag'] = temp_busyflag
    df['FlashADC_1'] = temp_adc1
    df['FlashADC_2'] = temp_adc2
    df['FlashADC_3'] = temp_adc3
    df['FlashADC_4'] = temp_adc4
    df['FlashADC_5'] = temp_adc5
    df['FlashADC_6'] = temp_adc6
    df['FlashADC_7'] = temp_adc7
    df['FlashADC_8'] = temp_adc8
    df['Event Number'] = df['Event Number'].astype('int32')
    df['NDAQ Number'] = df['NDAQ Number'].astype('int16')
    df['Slot Number'] = df['Slot Number'].astype('int8')
    df['Trigger Flags'] = df['Trigger Flags'].astype('int16')
    df['BusyFlag'] = df['BusyFlag'].astype('int8')
    
    name_file = 'AngraRun_TestRun_15m_'+ str(current_milli_time())+'.parq'
    #df.to_hdf(name_file,'a')
    print('Start building the Parquet File')
    df.to_parquet(name_file)
    return name_file

num = 0

def run_control():
    global num
    period = 15*60 + 30
    
    if ((num%2)==0): 
        memorypage = 2
        lastpage = 1
    else: 
        memorypage = 1
        lastpage = 2
    stop_trigger()
    time.sleep(2)
    start_daq(memorypage)
    time.sleep(2)
    start_trigger()
    print('Starting DAQ...')
    num+=1
    t1 = threading.Timer(period, run_control)
    t1.start()
    nam = save_file(lastpage)
    print('MemoryPage ' + str(lastpage) + ' saved to a file.')
    #p = subprocess.call('gzip '+nam, shell=True)
queue = RPiQueue()
queue.clear_all(1)
queue.clear_all(2)
run_control()

