#! /usr/bin/python3

import numpy as np
import pandas as pd
import glob

def separate_ndaqs(df):
    ndaq6 = df[(df['Slot Number']==6) & (df['BusyFlag']==0)]
    ndaq10 = df[(df['Slot Number']==10) & (df['BusyFlag']==0)]
    ndaq12 = df[(df['Slot Number']==12) & (df['BusyFlag']==0)]
    ndaq14 = df[(df['Slot Number']==14) & (df['BusyFlag']==0)]
    return ndaq6[:-1], ndaq10[:-1], ndaq12[:-1], ndaq14[:-1]
    
def align_data(ndaq6, ndaq10, ndaq12, ndaq14):
    i = 0
    j = 0
    k = 0
    l = 0
    aligned6 = []
    aligned10 = []
    aligned12 = []
    aligned14 = []
    
    slot6 = ndaq6['Timestamp'][1:]
    slot10 = ndaq10['Timestamp'][1:]
    slot12 = ndaq12['Timestamp'][1:]
    slot14 = ndaq14['Timestamp'][1:]
    
    for i in range(0,len(slot6)):
        value = slot6[slot6.index[i]]
        max_distortion = max(5,150*value/1000000)
        no_j = 0
        no_k = 0
        no_l = 0
        range_0 = min(20,len(slot10)-j)
        for m in range(j,j+range_0):
            if (abs(value - slot10[slot10.index[m]]))<max_distortion:
                j=m+1
                break
            if (m==j+range_0-1):
                no_j = 1
                break
        if range_0==0:
            no_j=1
        range_1 = min(20,len(slot12)-k)
        for m in range(k,k+range_1):
            if (abs(value - slot12[slot12.index[m]]))<max_distortion:
                k=m+1
                break
            if (m==k+range_1-1):
                no_k = 1
                break
        if range_1==0:
            no_k=1        
        range_2 = min(20,len(slot14)-l)
        for m in range(l,l+range_2):
            if (abs(value - slot14[slot14.index[m]]))<max_distortion:
                l=m+1
                break
            if (m==l+range_2-1):
                no_l = 1
                break
        if range_2==0:
            no_l=1
        
        si = slot6.index[i]
        sj = slot10.index[j-1]
        sk = slot12.index[k-1]
        sl = slot14.index[l-1]
        if (no_j == 0) and (no_k == 0) and (no_l == 0):
            aligned6.append(si)
            aligned10.append(sj)
            aligned12.append(sk)
            aligned14.append(sl)
    return aligned6, aligned10, aligned12, aligned14

def calculate_charge(ndaq,aligned):
    NDAQ = np.zeros((len(aligned),8))
    NDAQp = np.zeros((len(aligned),8))
    NDAQs = np.zeros((len(aligned),8))
    NDAQm = np.zeros((len(aligned),8))
    mask = np.array([1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    for i in range(0,8):
      matrix = np.stack(ndaq.loc[aligned]['FlashADC_'+str(1+i)].as_matrix(), axis=0)
      baseline = np.dot(matrix,mask)/mask.sum()
      carga = matrix.sum(axis=1) - baseline*matrix.shape[1]
      carga_p = (carga>0)*carga
      maximo = matrix.max(axis=1)
      sat = (maximo>126).astype(int)
      max_value = maximo - baseline
      NDAQ[:,i] = carga
      NDAQs[:,i] = sat
      NDAQm[:,i] = max_value
      NDAQp[:,i]=carga_p
    return NDAQ,NDAQs,NDAQm,NDAQp

def charge_matrix(aligned6, aligned10, aligned12, aligned14, ndaq6, ndaq10, ndaq12, ndaq14):
    saturated = 0
    NDAQ6,NDAQ6s,NDAQ6m,NDAQ6p = calculate_charge(ndaq6,aligned6)
    NDAQ10,NDAQ10s,NDAQ10m,NDAQ10p = calculate_charge(ndaq10,aligned10)
    NDAQ12,NDAQ12s,NDAQ12m,NDAQ12p = calculate_charge(ndaq12,aligned12)
    NDAQ14,NDAQ14s,NDAQ14m,NDAQ14p = calculate_charge(ndaq14,aligned14)

    total_charge = np.concatenate((NDAQ6,NDAQ10,NDAQ12,NDAQ14),axis=1).sum(axis=1)
    total_p_charge = np.concatenate((NDAQ6p,NDAQ10p,NDAQ12p,NDAQ14p),axis=1).sum(axis=1)
    saturated = np.concatenate((NDAQ6s,NDAQ10s,NDAQ12s,NDAQ14s),axis=1).sum(axis=1)
    sum_amplitude = np.concatenate((NDAQ6m,NDAQ10m,NDAQ12m,NDAQ14m),axis=1).sum(axis=1)
    return np.concatenate((total_charge.reshape(total_charge.shape[0],1), total_p_charge.reshape(total_p_charge.shape[0],1), NDAQ6,NDAQ10,NDAQ12,NDAQ14,saturated.reshape(saturated.shape[0],1),NDAQ6m,NDAQ10m,NDAQ12m,NDAQ14m,sum_amplitude.reshape(sum_amplitude.shape[0],1)),axis=1) 

def create_df(df):
    columns=['Event_Number','Timestamp1','Timestamp2','Timestamp3','Timestamp4', 'Event_Flag','Total_charge','Total_p_charge',
         'PMT01','PMT02','PMT03', 'PMT04','PMT05','PMT06','PMT07','PMT08','PMT09','PMT10',
         'PMT11','PMT12','PMT13', 'PMT14','PMT15','PMT16','PMT17','PMT18','PMT19','PMT20',
         'PMT21','PMT22','PMT23', 'PMT24','PMT25','PMT26','PMT27','PMT28','PMT29','PMT30',
         'PMT31','PMT32','Saturated','PMT01_Amplitude','PMT02_Amplitude','PMT03_Amplitude', 'PMT04_Amplitude','PMT05_Amplitude','PMT06_Amplitude','PMT07_Amplitude','PMT08_Amplitude','PMT09_Amplitude','PMT10_Amplitude',
         'PMT11_Amplitude','PMT12_Amplitude','PMT13_Amplitude', 'PMT14_Amplitude','PMT15_Amplitude','PMT16_Amplitude','PMT17_Amplitude','PMT18_Amplitude','PMT19_Amplitude','PMT20_Amplitude',
         'PMT21_Amplitude','PMT22_Amplitude','PMT23_Amplitude', 'PMT24_Amplitude','PMT25_Amplitude','PMT26_Amplitude','PMT27_Amplitude','PMT28_Amplitude','PMT29_Amplitude','PMT30_Amplitude',
         'PMT31_Amplitude','PMT32_Amplitude','Sum_Amplitude']
    
    ndaq6,ndaq10,ndaq12,ndaq14 = separate_ndaqs(df)
    ndaq6=ndaq6.reindex()
    ndaq10=ndaq10.reindex()
    ndaq12=ndaq12.reindex()
    ndaq14=ndaq14.reindex()
    a,b,c,d = align_data(ndaq6,ndaq10,ndaq12,ndaq14)
    k = charge_matrix(a,b,c,d,ndaq6,ndaq10,ndaq12,ndaq14)
    ev_number = np.array(ndaq6.loc[a]['Event Number'])
    timestamp1 = np.array(ndaq6.loc[a]['Timestamp'])
    timestamp2 = np.array(ndaq10.loc[b]['Timestamp'])
    timestamp3 = np.array(ndaq12.loc[c]['Timestamp'])
    timestamp4 = np.array(ndaq14.loc[d]['Timestamp'])
    flag = np.zeros(len(ev_number))
    for i in range(3,len(ev_number)-1):
        if ev_number[i]-ev_number[i-1] >1:
            flag[i]=1
    matrix = np.concatenate((ev_number.reshape(len(ev_number),1), timestamp1.reshape(len(timestamp1),1),timestamp2.reshape(len(timestamp2),1),timestamp3.reshape(len(timestamp3),1),timestamp4.reshape(len(timestamp4),1),flag.reshape(len(flag),1), k),axis=1)
    df = pd.DataFrame(matrix,columns=columns,dtype='int32')
    return df

def process_file(arquivo):
    df2 = pd.read_parquet('/data/data2/' + arquivo)
    df = create_df(df2)
    df.to_parquet('processed/'+arquivo[:-5]+'_processed_v4.parq')

f = open("lists/full_reactor_power_period_2_2019.csv", "r")
a = f.read()
lista_reactor_off = a.split('\n')[0].split(',')
del a

for arquivo in lista_reactor_off:
    try:
        process_file(arquivo)
    except:
        print('Falha ao processar aquivo: '+ arquivo)

