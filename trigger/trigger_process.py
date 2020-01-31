#!/usr/bin/python
# Trigger Process Script of the Angra System 
# Original version wrote by Jomas (2017)
# Version 4 : Integrated with Dash Monitor
# Responsible for this version: Herman Lima Jr. and Luis Fernando Gomez Gonzalez (2020)
# ----------------- Imports --------------------

# Current path
PATH_PWD = '/home/pi/'
# Required Libs
import threading
import time
import sys
sys.path.append(PATH_PWD)
# Required Libs SPI
import spidev
import spilibx
#<<---imports

#LF Import
import gc
gc.enable()
gc.set_debug(gc.DEBUG_LEAK)
flip = 0 

def dump_garbage():
    """
    show us what's the garbage about
    """
        
    # force collection
    print "\nGARBAGE:"
    gc.collect()

    print "\nGARBAGE OBJECTS:"
    for x in gc.garbage:
        s = str(x)
        if len(s) > 80: s = s[:80]
        print type(x),"\n  ", s

# Files Control
FILE_DATA_LOG_PATH = PATH_PWD + "log/DATA_LOG.LOG"
FILE_STAT_LOG_PATH = PATH_PWD + "log/STATUS_LOG.LOG"
FILE_CONFIG_FILE_PATH = PATH_PWD + "conf/TRIGGER.CONF"
FILE_RUN_STATUS_PATH = PATH_PWD + "conf/RUN.CONF"
FILE_VERSION_PROG_PATH = PATH_PWD + "conf/VERSION.CONF"
FILE_IDD_RUN_NUMBER_PATH = PATH_PWD + "log/IDD_RUN_LOG.LOG"
#<ctrl


# Global Variables
RESET_FPGA_MASTER = False
TIME_START_RUNN = 0.0
FIRST_START_FLG = True
#<glob


# Buffer to DATA Aquisition
RC_BUFFER_FROM_SPI = []
# Initialize and Fill the Buffer
NUM_BYTES_FRAME = 43
for x in range(0, NUM_BYTES_FRAME):
    RC_BUFFER_FROM_SPI.append('00000000')
#<dacq


# Expected Values Frames: RX
EXPECTED_PREAMBULE = ['00000000', '11111111', '11111111', '11111111', '10011101']
EXPECTED_END_OF = ['11111111', '00000000']
#<exptd


# Buffer to Receive Values from FPGA
def BUFFER_RECEIVED_VAL (value_push):
    global FILE_IDD_RUN_NUMBER_PATH
    global RC_BUFFER_FROM_SPI
    global RESET_FPGA_MASTER
    global TIME_START_RUNN
    global FIRST_START_FLG
    global EXPECTED_PREAMBULE
    global NUM_BYTES_FRAME
    global EXPECTED_END_OF
    global FILE_DATA_LOG_PATH
    global FILE_STAT_LOG_PATH
    # For Data Acquistion Buffer
    # Add in the end of Queue DAQ
    RC_BUFFER_FROM_SPI.append(value_push)
    # Remove the firs (older) DAQ
    RC_BUFFER_FROM_SPI.pop(0)
    #print RC_BUFFER_FROM_SPI
    # Use a aux value
    AUX_BUFFER_RX_SPI = []
    AUX_BUFFER_RX_SPI.extend(RC_BUFFER_FROM_SPI)
    if AUX_BUFFER_RX_SPI[0:5] == EXPECTED_PREAMBULE and AUX_BUFFER_RX_SPI[(NUM_BYTES_FRAME-2):(NUM_BYTES_FRAME)] == EXPECTED_END_OF:
        # Time
        time_local = time.time()
        # print only
        gc.collect()
        print "----------->>> OK >>> -----------------------------"
        #dump_garbage()
        # Convert to Space and Capture the RUN IDD
        RUN_IDD_C = spilibx.READ_ONLY_FIRST_LINE(FILE_IDD_RUN_NUMBER_PATH)
        # Check if RUNNING
        if RESET_FPGA_MASTER == True:
            AUX_SPACE_RX_BUFF = ''
            if ( FIRST_START_FLG == True ):
                AUX_SPACE_RX_BUFF = RUN_IDD_C + " " + spilibx.RX_COMPOSE_STATUS( AUX_BUFFER_RX_SPI, TIME_START_RUNN )
                FIRST_START_FLG = False
            else:
                AUX_SPACE_RX_BUFF = RUN_IDD_C + " " + spilibx.RX_COMPOSE_STATUS( AUX_BUFFER_RX_SPI, time_local )
            # Save the LOG Values
            spilibx.SAVE_LOG_FILE_ALL( FILE_DATA_LOG_PATH, AUX_SPACE_RX_BUFF )
        # Save the STATUS (Converted to Humans)
        spilibx.SAVE_LOG_OVERWRITE_W( FILE_STAT_LOG_PATH, RUN_IDD_C + " " + spilibx.RX_COMPOSE_STATUS( AUX_BUFFER_RX_SPI, time_local ) )
#<buffrx


# Current State Control
STATE_CONTROL = 'INIT_ST'
#<st

# Vars Clear
FULL_FRAME_PKT=['00000000']
index_tx = 0
#<vars



# ------ RPI GPIO Declaration ------
# Import the RPI and set the gpio map
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
# Define the Pin Name
FPGA_MASTER_RSTN = 15
FPGA_COMMU_RSTN = 18
FPGA_RUN_LED_RUNST = 16
# Define the Directions
# OUTPUT (MAIN FPGA RESET ) --> GPIO 22 (fisico RPI 15) (Ligado ao 29 (34 fisico) do Slot 2 FPGA)
GPIO.setup(FPGA_MASTER_RSTN, GPIO.OUT)
# OUTPUT (ENABLE FPGA RUN) --> GPIO 24 (fisico RPI 18) (Ligado ao 31 (36 fisico ) do Slot 2 FPGA
GPIO.setup(FPGA_COMMU_RSTN, GPIO.OUT)
# OUTPUT (LAD RUN STATUS ) --> GPIO 23 (fisico RPI 16) (Ligado ao 30 (35 fisico) do Slot 2 FPGA)
GPIO.setup(FPGA_RUN_LED_RUNST, GPIO.OUT)

# --------- RESET ALL ---------
# Reset All with True
time.sleep(0.1)
GPIO.output(FPGA_MASTER_RSTN, True)
GPIO.output(FPGA_COMMU_RSTN, True)
time.sleep(0.1)
GPIO.output(FPGA_MASTER_RSTN, False)
GPIO.output(FPGA_COMMU_RSTN, False)
time.sleep(0.1)
GPIO.output(FPGA_MASTER_RSTN, True)
GPIO.output(FPGA_COMMU_RSTN, True)
time.sleep(0.1)
# LEDs
GPIO.output(FPGA_RUN_LED_RUNST, False)
# RESET FLAG
RESET_FPGA_MASTER = False
# Time Sleep to Reset
time.sleep(0.1)
#<gpio




# Main Procedure
while True:
    #
    
    # ------ State Control -----
    if STATE_CONTROL == 'INIT_ST':
        # Clear ALL
        # Reset ALL
        # Clear RUN FILE
        spilibx.SAVE_DATA_LOG_ANALYSIS(FILE_RUN_STATUS_PATH, '0')
        # Clear the STATUS
        ret_str = '1' + ' ' + '0' + ' ' + '0' + ' ' + '0' + ' ' + '0' + ' ' + '0' + ' ' + '0000' + ' ' + '00000000' + ' ' + '00000000000000000000000000000000' + ' ' + '0' + ' ' + '0' + ' ' + '0' + ' ' + '00000000000000000000000000000000000000000000000000000000'
        spilibx.SAVE_LOG_OVERWRITE_W( FILE_STAT_LOG_PATH, ret_str )
        
        # Next State
        STATE_CONTROL = 'WAIT_RUN_ST'
        # 
    #
    # Wait RUN == 1
    elif STATE_CONTROL == 'WAIT_RUN_ST':
        # Read the RUN Status
        RUN_STATUS = spilibx.LOAD_RUN_STATUS_FILE(FILE_RUN_STATUS_PATH)
        # Check Go to if Config == 1
        if RUN_STATUS == '1':
            STATE_CONTROL = 'CONFIGURE_FPGA_ST'
            # Clear
            index_tx = 0
        # Go to RUN == 2
        elif RUN_STATUS == '2':
            # Go to RUNNING
            STATE_CONTROL = 'RUNNING_FPGA_ST'
            # Time Start RUN
            TIME_START_RUNN = time.time()
            # Active the First Time FLAG - to Save the Initial Time (n-syn from fpga)
            FIRST_START_FLG = True
            # 
            # Reset Master
            time.sleep(0.1)
            GPIO.output(FPGA_MASTER_RSTN, True)
            time.sleep(0.1)
            GPIO.output(FPGA_MASTER_RSTN, False)
            time.sleep(0.1)
            GPIO.output(FPGA_MASTER_RSTN, True)
            time.sleep(0.1)
            #
        #
        #> Change the Time Log <#
        RESET_FPGA_MASTER = False
        # LEDs OFF
        GPIO.output(FPGA_RUN_LED_RUNST, False)
    #
    # Collect the CONFIG DATA and RESET the VALUE
    elif STATE_CONTROL == 'CONFIGURE_FPGA_ST':
        # Prepare the data to SEND
        # 1. Load the Confif File
        conf_loaded = spilibx.LOAD_CONF_FILE (FILE_CONFIG_FILE_PATH)
        # 2. Mount the Packet Frame
        frame_mounted = spilibx.MOUNT_PKT_FROM_DECFILE (conf_loaded)
        # 3. FULL Packet Mounted TX
        FULL_FRAME_PKT = spilibx.TX_FULL_PACKET_TO_FPGA (frame_mounted)
        #
        # Reset the Comunication Flags
        time.sleep(0.1)
        GPIO.output(FPGA_COMMU_RSTN, True)
        time.sleep(0.1)
        GPIO.output(FPGA_COMMU_RSTN, False)
        time.sleep(0.1)
        GPIO.output(FPGA_COMMU_RSTN, True)
        time.sleep(0.1)
        #        
        # Next State
        STATE_CONTROL = 'TX_CONFG_FPGA_ST'
    #
    # Transmit Configuration to FPGA
    elif STATE_CONTROL == 'TX_CONFG_FPGA_ST':
        # Collect the Number of PKTs
        MAX_NUMB_OF_PKT = len(FULL_FRAME_PKT)
        if index_tx < (MAX_NUMB_OF_PKT - 1):
            index_tx = index_tx + 1
        # Go Back to WAIT RUN 
        else:
            # Next State
            STATE_CONTROL = 'WAIT_RUN_ST'
            # Go the RUN FILE to 0 == WAIT
            spilibx.SAVE_DATA_LOG_ANALYSIS(FILE_RUN_STATUS_PATH, '0')
        #
    # Reset ALL FPGA Board
    elif STATE_CONTROL == 'RUNNING_FPGA_ST':
        
        # LEDs On RUN
        #GPIO.output(FPGA_RUN_LED_RUNST, True)
        if True: #(flip>0):
            GPIO.output(FPGA_RUN_LED_RUNST, True)
            #time.sleep(0.001)
            #GPIO.output(FPGA_RUN_LED_RUNST, False)
            #flip = 0
        else:
            #time.sleep(0.001)
            GPIO.output(FPGA_RUN_LED_RUNST, False)
            flip += 1
        
        #> Change the Time Log <#
        RESET_FPGA_MASTER = True
        # Read the RUN Status
        RUN_STATUS = spilibx.LOAD_RUN_STATUS_FILE(FILE_RUN_STATUS_PATH)
        # Check if STOP == 0
        if RUN_STATUS == '0':
            STATE_CONTROL = 'WAIT_RUN_ST'
    #
    #
    # ---- RX : TX Process ----
    # Send and Receive SPI
    RX_VALUE_FROM_FPGA = spilibx.spi_loop(FULL_FRAME_PKT[index_tx])
    # Add in the QUEUE BUFFER
    BUFFER_RECEIVED_VAL(RX_VALUE_FROM_FPGA)

    time.sleep(0.001)

