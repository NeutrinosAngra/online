#!/usr/bin/python
# SPI LIB of the Angra System 
# Original version wrote by Jomas (2017)

# Required Libs
import spidev
import time
import sys
#<imports


# ------------------------ Basic Functions  -----------------------

# Bin to Int
def bin2int (binvalue):
    # Check the size
    q=len(binvalue)-1
    # initial value
    ret=0
    # Loop for Calculate
    for i in binvalue[:]:
        # Build the Exponent Value
        e=2**q
        # Iterate the i with the exponent
        n=int(i)*e
        # Sum with the returned value
        ret=ret+n
        # decrease the q position weighted
        q=q-1
    # Return the integer
    return ret
#b2i

# Int to Bin
def int2bin (intv_in):
    #Initial Value
    ret=''
    # Convert to int
    intv = int(intv_in)
    # Loop to convert
    while True:
        vl=intv%2
        intv=intv/2
        intv=int(intv)
        ret=str(vl)+ret
        if intv==0:
            break
    #
    # Insert 0 at left side
    zero='00000000'
    concat=zero+ret
    # calculate the length
    q=len(concat)
    # Trunc the value based on the length
    trunc=concat[q-8:q]
    # Return
    return trunc
#i2b

# Reverse Bits
def reversebits (binvalue):
    # Insert - at left side
    zero='00000000'
    concat=zero+binvalue
    # calculate the length
    q=len(concat)
    # Trunc the value based on the length
    trunc=concat[q-8:q]
    # initial value
    ret=''
    # Loop for Calculate
    for i in trunc[:]:
        ret=i+ret
    #
    # Return
    return ret
#rb

# Convert DEC to BIN with NBits. Ex: 2 to 00000010
def conv_dec_to_bin (intv_in, outlen):
    #Initial Value
    ret=''
    # Convert to int
    intv = int(intv_in)
    # Loop to convert
    while True:
        vl=intv%2
        intv=intv/2
        intv=int(intv)
        ret=str(vl)+ret
        if intv==0:
            break
    # Format the output
    zero='00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    concat=zero+ret
    endval=len(concat)
    staval=endval-outlen
    return concat[staval:endval]
# <end

# Convert List to String: ['00', '01', '02'] --> '00 01 02'
def conv_list_to_str_spac (list_vl):
    ret_str=''
    for x in xrange(len(list_vl)):
        if x == 0:
            ret_str=list_vl[x]
        else:
            ret_str=ret_str+" "+list_vl[x]
    return ret_str
# <end

# Convert to Unic STR: ['00', '01', '02'] --> '000102'
def conv_list_to_unic_str (list_vl):
    ret_str=''
    for x in xrange(len(list_vl)):
        if x == 0:
            ret_str=list_vl[x]
        else:
            ret_str=ret_str+list_vl[x]
    return ret_str
# <end

# ------------------------------ SPI ------------------------------
spi = spidev.SpiDev()

# SPI Transmission
def spi_loop (value_sent_in):
    global spi
    # Send and receive the data though SPI
    try:
        # Initialize the SPI
        #spi = spidev.SpiDev()
        spi.open(0, 1)
        # Max Speed 8MHZ - Because the System is 50Mhz - Slack of 6times
        spi.max_speed_hz=8000000
        #
        # Reverse Bits
        sentv_rev = reversebits(value_sent_in)
        # Convert to Integer
        sentv_int = bin2int(sentv_rev)
        # The Reverse bits is transparent for Rasp and FPGA
        rece_fpga = spi.xfer([sentv_int])
        spi.close()
        rece_int = int(rece_fpga[0])
        rece_bin = int2bin(rece_int)
        rece_rev = reversebits(rece_bin)
        return rece_rev
    except:
        # Return None
        return None
#spit

# ---------------------------- Packet -----------------------------


# Compose the Packet to Status
def RX_COMPOSE_STATUS (rx_frame_in, TIME_STAMP_VAL):
    # Collect the Data Frame (remove preamble and end) total 36 Packets
    PACKET_FR = rx_frame_in[5:41]
    # Split the Frames
    # --- 1. ERROR - INTEGER
    ERROR_SPI = PACKET_FR[0][2]
    MLT_TRIGGER_i = PACKET_FR[0][3]
    ENE_TRIGGER_i = PACKET_FR[0][4]
    SHIELD_VT_i = PACKET_FR[0][5]
    VETO_UP_i = PACKET_FR[0][6]
    VETO_BOTT_i = PACKET_FR[0][7]
    # --- 2. PMTs Status
    # Conv to unic
    pmts_val = PACKET_FR[1:7]
    unic_bits = conv_list_to_unic_str (pmts_val)
    # Split in Parts
    # SHIELD PMTS
    pmtp1_shield = unic_bits[4:8]
    # VETO PMTS
    pmtp2_vetos = unic_bits[8:16]
    # DETECTOR CENTRAL PMTs
    pmtp3_detct = unic_bits[16:48]
    # ---- 3. Counters and Timers / Reserved
    # Event TRIG NUMB
    EVNT_TRG_NUMB = bin2int(conv_list_to_unic_str(PACKET_FR[8:14])) # Original 7:14
    # Herman Header
    HermanHeader = bin2int(conv_list_to_unic_str(PACKET_FR[7:8])) # 
    # Veto TRIG NUMB
    EVNT_TG_VET_NUMB = bin2int(conv_list_to_unic_str(PACKET_FR[14:21]))
    # RESERVED VAL 1 = 56 bits
    RESERVED_VAL_1 = bin2int(conv_list_to_unic_str(PACKET_FR[21:28]))
    # RESERVED VAL 2 = 64 bits
    RESERVED_VAL_2 = bin2int(conv_list_to_unic_str(PACKET_FR[7:8]+PACKET_FR[28:36]))
    # Return the Composed Value
    ret_str=''
    ret_str = ERROR_SPI + ' ' + MLT_TRIGGER_i + ' ' + ENE_TRIGGER_i + ' ' + SHIELD_VT_i + ' ' + VETO_UP_i + ' ' + VETO_BOTT_i + ' ' + pmtp1_shield + ' ' + pmtp2_vetos + ' ' + pmtp3_detct + ' ' + str(EVNT_TRG_NUMB) + ' ' + str(EVNT_TG_VET_NUMB) + ' ' + str(RESERVED_VAL_1) + ' '+ str(RESERVED_VAL_2) + ' ' + repr(TIME_STAMP_VAL)
    return ret_str
#


# Decode the Conf FILE (5ns)
# Add the TIME STAMP ***** (Future)
def MOUNT_PKT_FROM_DECFILE (all_pakeck_list):
    # Assign the values from CONF FILE
    [MAXW_LEN_CD, DT_WINDOW_CD, UP_COINC_TRESHOLD, DOWN_COINC_TRESHOLD, CL_PARAM, TK_SEL_PARAM, TK_DEC_PARAM, DW_SH_THRS, DW_VT_UP_THRS, DW_VT_BOTT_THRS, VS_PARAM, DT_WINDOW_VT, DT_WINDOW_VH, VS_SEL_PARAM, VS_OLEN_PARAM, VS_BLK_PARAM, BLOCK_CHANNEL_SH, BLOCK_CHANNEL_VT_UP, BLOCK_CHANNEL_VT_BOT, BLOCK_CHANNEL_DC_UP, BLOCK_CHANNEL_DC_BOT, DWN_SCL_WINDOW, RESERVED1, RESERVED2,DEAD_TIME ] = all_pakeck_list
    # 
    # Clear the packet
    packet = []
    # Frequency time to convert to number of clocks
    freq = 5;
    # Convert the Values
    packet.append(conv_dec_to_bin(int(MAXW_LEN_CD)/freq, 8))
    packet.append(conv_dec_to_bin(int(DT_WINDOW_CD)/freq, 8))
    packet.append(conv_dec_to_bin(int(UP_COINC_TRESHOLD), 8))
    packet.append(conv_dec_to_bin(int(DOWN_COINC_TRESHOLD), 8))
    packet.append(conv_dec_to_bin(int(CL_PARAM)/freq, 8))
    # Join TK_SEL_PARAM and TK_DEC_PARAM
    packet.append(conv_dec_to_bin(int(TK_SEL_PARAM), 2) + conv_dec_to_bin(int(TK_DEC_PARAM)/freq, 6))
    # Join DW_SH_THRS and DW_VT_UP_THRS
    packet.append('00' + conv_dec_to_bin(int(DW_SH_THRS), 3) + conv_dec_to_bin(int(DW_VT_UP_THRS), 3))
    # Join the DW_VT_BOTT_THRS + VS_PARAM
    packet.append(conv_dec_to_bin(int(DW_VT_BOTT_THRS), 3) + conv_dec_to_bin(int(VS_PARAM)/freq, 5))
    # DT WINDOWS VETO
    packet.append(conv_dec_to_bin(int(DT_WINDOW_VT)/freq, 8))
    packet.append(conv_dec_to_bin(int(DT_WINDOW_VH)/freq, 8))
    # Join the VS_SEL_PARAM and VS_OLEN_PARAM
    packet.append(conv_dec_to_bin(int(VS_SEL_PARAM), 3) + conv_dec_to_bin(int(VS_OLEN_PARAM)/freq, 5))
    # Split the VETO BLOCK TIME in TWO BYTES
    part_blkk = conv_dec_to_bin(int(VS_BLK_PARAM)/freq, 16)
    packet.append(part_blkk[0:8])
    packet.append(part_blkk[8:16])
    # Mount the block 44
    # Frist Byte BLOCK CHANNEL 4 bits from SHIELD
    packet.append('0000'+BLOCK_CHANNEL_SH)
    # Second Byte BLOCK CHANNEL = Veto UP + Veto BOT
    packet.append(BLOCK_CHANNEL_VT_UP+BLOCK_CHANNEL_VT_BOT)
    # Third Byte BLOCK CHANNEL = DC UP + DC DOWN -> Slit in bythes
    packet.append(BLOCK_CHANNEL_DC_UP[0:8])
    packet.append(BLOCK_CHANNEL_DC_UP[8:16])
    packet.append(BLOCK_CHANNEL_DC_BOT[0:8])
    packet.append(BLOCK_CHANNEL_DC_BOT[8:16])
    # Downscale slipt in 2
    part_left=conv_dec_to_bin(int(DWN_SCL_WINDOW)/freq, 16)
    packet.append(part_left[0:8])
    packet.append(part_left[8:16])
    # Reserved
    # RESERVED1 = NULL 1 bytes
    packet.append(RESERVED1[0:8])
    packet.append(RESERVED1[8:16])
    packet.append(RESERVED1[16:24])
    packet.append(RESERVED1[24:32])
    packet.append(RESERVED1[32:40])
    packet.append(RESERVED1[40:48])
    packet.append(RESERVED1[48:56])
    # RESERVED2 = NULL 8 bytes
    packet.append(RESERVED2[0:8])
    packet.append(RESERVED2[8:16])
    packet.append(RESERVED2[16:24])
    packet.append(RESERVED2[24:32])
    packet.append(RESERVED2[32:40])
    packet.append(RESERVED2[40:48])
    packet.append(RESERVED2[48:56])
    packet.append(RESERVED2[56:64])
    # DEAD TIME
    part_deadtime=conv_dec_to_bin(int(DEAD_TIME)/freq, 16)
    packet.append(part_deadtime[0:8])
    packet.append(part_deadtime[8:16])

    # return all
    return packet
#<dec


# Mount the Packet TX to Rasp = Preambule + ADDRESS + Frame + End
def TX_FULL_PACKET_TO_FPGA (paket_list):
    tx_packet = []
    # Preambule
    preambule_pkt = ['00000000', '11111111', '11111111', '11111111', '11111111', '10101011' ]
    # ADDRESS 16 bits = 2 bytes
    # Number of frames (Automatic)
    number_of_frames=len(paket_list)
    address_full=conv_dec_to_bin(int(number_of_frames), 16)
    address_1 = address_full[0:8]
    address_2 = address_full[8:16]
    # End
    end_pkt = ['11111111', '00000000']
    # ----- Join All ----
    tx_packet.extend (preambule_pkt)
    tx_packet.append (address_1)
    tx_packet.append (address_2)
    tx_packet.extend (paket_list)
    tx_packet.extend (end_pkt)
    # Return Packet
    return tx_packet
#<full


# ----------------------------- SAVE/LOAD ------------------------------


# Save the DATA LOG to Analysis
def SAVE_LOG_FILE_ALL (file_name, data_log_in):
    # Open to Append
    conf_target = open(file_name , 'a')
    # Write
    conf_target.write(str(data_log_in)+'\n')
    # Close
    conf_target.close()
#


# SAVE STATUS LOG
def SAVE_LOG_OVERWRITE_W (file_name, data_log_in):
    # Open to Append
    conf_target = open(file_name , 'w')
    # Write
    conf_target.write(str(data_log_in))
    # Close
    conf_target.close()
#

# LOAD and DECODE STATUS LOG
def LOAD_DECODE_STATUS_LOG (file_name):
    # 1. LOAD
    # Open to Read
    conf_target = open(file_name , 'r')
    # Read All
    STATUS_LOG = conf_target.readline().split('\n')[0]
    # Close
    conf_target.close()
    # 2. DECODE
    
    
    # Return
    return STATUS_LOG
#


# LOAD the CONF FILE
def LOAD_CONF_FILE (file_name):
    # Open to Read
    conf_target = open(file_name , 'r')
    # Read ALL
    # Remove the lsft side from = and follow the parameter sequence from line number
    MAXW_LEN_CD = conf_target.readline().split('\n')[0].split('=')[1]
    DT_WINDOW_CD = conf_target.readline().split('\n')[0].split('=')[1]
    UP_COINC_TRESHOLD = conf_target.readline().split('\n')[0].split('=')[1]
    DOWN_COINC_TRESHOLD = conf_target.readline().split('\n')[0].split('=')[1]
    CL_PARAM = conf_target.readline().split('\n')[0].split('=')[1]
    TK_SEL_PARAM = conf_target.readline().split('\n')[0].split('=')[1]
    TK_DEC_PARAM = conf_target.readline().split('\n')[0].split('=')[1]
    DW_SH_THRS = conf_target.readline().split('\n')[0].split('=')[1]
    DW_VT_UP_THRS = conf_target.readline().split('\n')[0].split('=')[1]
    DW_VT_BOTT_THRS = conf_target.readline().split('\n')[0].split('=')[1]
    VS_PARAM = conf_target.readline().split('\n')[0].split('=')[1]
    DT_WINDOW_VT = conf_target.readline().split('\n')[0].split('=')[1]
    DT_WINDOW_VH = conf_target.readline().split('\n')[0].split('=')[1]
    VS_SEL_PARAM = conf_target.readline().split('\n')[0].split('=')[1]
    VS_OLEN_PARAM = conf_target.readline().split('\n')[0].split('=')[1]
    VS_BLK_PARAM = conf_target.readline().split('\n')[0].split('=')[1]
    BLOCK_CHANNEL_SH = conf_target.readline().split('\n')[0].split('=')[1]
    BLOCK_CHANNEL_VT_UP = conf_target.readline().split('\n')[0].split('=')[1]
    BLOCK_CHANNEL_VT_BOT = conf_target.readline().split('\n')[0].split('=')[1]
    BLOCK_CHANNEL_DC_UP = conf_target.readline().split('\n')[0].split('=')[1]
    BLOCK_CHANNEL_DC_BOT = conf_target.readline().split('\n')[0].split('=')[1]
    DWN_SCL_WINDOW = conf_target.readline().split('\n')[0].split('=')[1]
    # Reserved
    RESERVED1 = conf_target.readline().split('\n')[0].split('=')[1]  
    RESERVED2 = conf_target.readline().split('\n')[0].split('=')[1]
    DEAD_TIME = conf_target.readline().split('\n')[0].split('=')[1]
    # Close
    conf_target.close()
    # Return
    return [ MAXW_LEN_CD, DT_WINDOW_CD, UP_COINC_TRESHOLD, DOWN_COINC_TRESHOLD, CL_PARAM, TK_SEL_PARAM, TK_DEC_PARAM, DW_SH_THRS, DW_VT_UP_THRS, DW_VT_BOTT_THRS, VS_PARAM, DT_WINDOW_VT, DT_WINDOW_VH, VS_SEL_PARAM, VS_OLEN_PARAM, VS_BLK_PARAM, BLOCK_CHANNEL_SH, BLOCK_CHANNEL_VT_UP, BLOCK_CHANNEL_VT_BOT, BLOCK_CHANNEL_DC_UP, BLOCK_CHANNEL_DC_BOT, DWN_SCL_WINDOW, RESERVED1, RESERVED2, DEAD_TIME ]
#

# Read the RUN PARAMETER
def LOAD_RUN_STATUS_FILE (file_name):
    # Open to Read
    conf_target = open(file_name , 'r')
    # Read All
    RUN_VALUE = conf_target.readline().split('\n')[0]
    # Close
    conf_target.close()
    # Return
    return RUN_VALUE
#

# Save the RUN PARAMETER
def SAVE_DATA_LOG_ANALYSIS (file_name, run_param_in):
    # Open to Append
    conf_target = open(file_name , 'w')
    # Write
    conf_target.write(str(run_param_in))
    # Close
    conf_target.close()
#


# READ Only the FIRST Line
def READ_ONLY_FIRST_LINE (file_name):
    # Open to Read
    conf_target = open(file_name , 'r')
    # Read All
    RUN_VALUE = conf_target.readline().split('\n')[0]
    # Close
    conf_target.close()
    # Return
    return RUN_VALUE
#

# SAVE only the FIRST Line
def SAVE_ONLY_FIRST_LINE (file_name, data_log_in):
    # Open to Append
    conf_target = open(file_name , 'w')
    # Write
    conf_target.write(str(data_log_in))
    # Close
    conf_target.close()
#

#By Jomas Scripts
