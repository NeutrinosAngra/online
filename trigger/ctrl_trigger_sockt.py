#!/usr/bin/python
# Control Trigger by TCP Sockets of the Angra System 
# Original version wrote by Jomas (2017)
# Version 2 : Integrated with RunControl
# Responsible for this version: Herman Lima Jr. and Luis Fernando Gomez Gonzalez (2020)

# Current path
PATH_PWD = '/home/pi/'
# Required Libs
import socket
import time
import sys
import os
sys.path.append(PATH_PWD)
# Required Libs SPI
import spidev
import spilibx
#<<---imports


# Files Control
FILE_DATA_LOG_PATH = PATH_PWD + "log/DATA_LOG.LOG"
FILE_STAT_LOG_PATH = PATH_PWD + "log/STATUS_LOG.LOG"
FILE_CONFIG_FILE_PATH = PATH_PWD + "conf/TRIGGER.CONF"
FILE_RUN_STATUS_PATH = PATH_PWD + "conf/RUN.CONF"
FILE_VERSION_PROG_PATH = PATH_PWD + "conf/VERSION.CONF"
FILE_IDD_RUN_NUMBER_PATH = PATH_PWD + "log/IDD_RUN_LOG.LOG"
#<ctrl


# STATUS COMMAND
def STATUS_COMMAND ():
    global FILE_STAT_LOG_PATH
    global FILE_IDD_RUN_NUMBER_PATH
    read_current = spilibx.READ_ONLY_FIRST_LINE(FILE_IDD_RUN_NUMBER_PATH)
    format_ret = spilibx.LOAD_DECODE_STATUS_LOG(FILE_STAT_LOG_PATH)
    return format_ret
#<buffrx

# CONNECTED CMD
def CONNECTED_CMD_STS ():
    global FILE_VERSION_PROG_PATH
    verstion_p = spilibx.READ_ONLY_FIRST_LINE(FILE_VERSION_PROG_PATH)
    return verstion_p
#<conn


# READY CMD
def READY_CMD_STS ():
    global FILE_IDD_RUN_NUMBER_PATH
    # Read
    read_current = spilibx.READ_ONLY_FIRST_LINE(FILE_IDD_RUN_NUMBER_PATH)
    # Increment
    idd_inc = int(read_current) + 1
    # Save Number Incremented
    spilibx.SAVE_ONLY_FIRST_LINE(FILE_IDD_RUN_NUMBER_PATH, idd_inc)
    # Compose the Answer and return
    ret_val = 'RUN ID NUMBER: ' + str(idd_inc)
    return ret_val
#<conn


# ------ IP and PORT ------
# Collect the IP
# SERVER IP Automaticall
MY_IP_FROM_LINUX = os.popen("ifconfig eth0 | grep 'inet addr' | cut -d ':' -f2 | cut -d ' ' -f1").read().split('\n')[0]
# Other Way to get the IP
#MY_IP_FROM_LINUX = socket.gethostbyname(socket.gethostname())
#<ip

# Define the IP
HOST = MY_IP_FROM_LINUX       # SERVER IP Address
PORT = 5000                   # Port
#<ip

# Initial State
STATE_CTRL = 'START_ST'

# List of acceptable param
valid_param_list = ['I', 'i', 'L', 'l', 'S', 's', 'P', 'p', 'R', 'r', 'Q', 'q', 'H', 'h']
#<lst

# Main Process
while True:
    # Add the realiability Try and Except
    try:
        # Define the Socket
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        orig = (HOST, PORT)
        tcp.bind(orig)
        tcp.listen(1)
        while True:
            # Accept only 1 one connetion from SUPERVISORIO
            con, cliente = tcp.accept()
            print 'Connected by: ', cliente
            while True:
                # 
                # Collect the MSG from SUPERVISORIO
                MSG_FROM_SUP = con.recv(4096)
                # -- Check if there are no MSG and BREAK to CLOSE the Connection and Sstablish Again
                if not MSG_FROM_SUP:
                    break
                #<-check
                
                # ---------------------------------- State Machine ----------------------------------
                
                # Execute only with valid commmands 
                if MSG_FROM_SUP in valid_param_list:
                    #
                    # ------------- NEXT START STATE LOGIC --------------
                    if STATE_CTRL == 'START_ST':
                        # Next State Logic
                        if MSG_FROM_SUP in ['I', 'i']:
                            STATE_CTRL = 'CONNECTED_ST'
                        #
                        # STATUS -- ALL STAGES
                        elif MSG_FROM_SUP in ['S', 's']:
                            # <<<--- Reply to SUPERVISORIO
                            con.send (STATE_CTRL + "\n" + STATUS_COMMAND())
                            print "-- (S) = STATUS REQUESTED"
                            # Go back to Beginning
                            continue
                        # QUIT WAY -- ALL STAGES
                        elif MSG_FROM_SUP in ['Q', 'q']:
                            STATE_CTRL = 'QUIT_ST'
                        else:
                            # <<<--- Reply to SUPERVISORIO
                            con.send ("Invalid Command : " +STATE_CTRL)
                            print "...Invalid Command ("+MSG_FROM_SUP+") : " +STATE_CTRL
                            # Go back to Beginning
                            continue
                    #
                    # CONNECTED STATE
                    elif STATE_CTRL == 'CONNECTED_ST':
                        # Next State Logic
                        if MSG_FROM_SUP in ['L', 'l']:
                            STATE_CTRL = 'CONFIGURED_ST'
                        #
                        # STATUS -- ALL STAGES
                        elif MSG_FROM_SUP in ['S', 's']:
                            # <<<--- Reply to SUPERVISORIO
                            con.send (STATE_CTRL + "\n" + STATUS_COMMAND())
                            print "-- (S) = STATUS REQUESTED"
                            # Go back to Beginning
                            continue
                        # QUIT WAY -- ALL STAGES
                        elif MSG_FROM_SUP in ['Q', 'q']:
                            STATE_CTRL = 'QUIT_ST'
                        else:
                            # <<<--- Reply to SUPERVISORIO
                            con.send ("Invalid Command : " +STATE_CTRL)
                            print "...Invalid Command ("+MSG_FROM_SUP+") : " +STATE_CTRL
                            # Go back to Beginning
                            continue
                    #
                    # CONFIGURED STATE
                    elif STATE_CTRL == 'CONFIGURED_ST':
                        # Next State Logic
                        if MSG_FROM_SUP in ['P', 'p']:
                            STATE_CTRL = 'READY_ST'
                        #
                        # STATUS -- ALL STAGES
                        elif MSG_FROM_SUP in ['S', 's']:
                            # <<<--- Reply to SUPERVISORIO
                            con.send (STATE_CTRL + "\n" + STATUS_COMMAND())
                            print "-- (S) = STATUS REQUESTED"
                            # Go back to Beginning
                            continue
                        # QUIT WAY -- ALL STAGES
                        elif MSG_FROM_SUP in ['Q', 'q']:
                            STATE_CTRL = 'QUIT_ST'
                        else:
                            # <<<--- Reply to SUPERVISORIO
                            con.send ("Invalid Command : " +STATE_CTRL)
                            print "...Invalid Command ("+MSG_FROM_SUP+") : " +STATE_CTRL
                            # Go back to Beginning
                            continue
                    #
                    # READY STATE
                    elif STATE_CTRL == 'READY_ST':
                        # Next State Logic
                        if MSG_FROM_SUP in ['R', 'r']:
                            STATE_CTRL = 'RUNNING_ST'
                        #
                        # STATUS -- ALL STAGES
                        elif MSG_FROM_SUP in ['S', 's']:
                            # <<<--- Reply to SUPERVISORIO
                            con.send (STATE_CTRL + "\n" + STATUS_COMMAND())
                            print "-- (S) = STATUS REQUESTED"
                            # Go back to Beginning
                            continue
                        # QUIT WAY -- ALL STAGES
                        elif MSG_FROM_SUP in ['Q', 'q']:
                            STATE_CTRL = 'QUIT_ST'
                        else:
                            # <<<--- Reply to SUPERVISORIO
                            con.send ("Invalid Command : " +STATE_CTRL)
                            print "...Invalid Command ("+MSG_FROM_SUP+") : " +STATE_CTRL
                            # Go back to Beginning
                            continue
                    #
                    # RUNNING STATE
                    elif STATE_CTRL == 'RUNNING_ST':
                        # Next State Logic 1 (go to READY)
                        if MSG_FROM_SUP in ['H', 'h']:
                            STATE_CTRL = 'READY_ST'
                        #
                        # STATUS -- ALL STAGES
                        elif MSG_FROM_SUP in ['S', 's']:
                            # <<<--- Reply to SUPERVISORIO
                            con.send (STATE_CTRL + "\n" + STATUS_COMMAND())
                            print "-- (S) = STATUS REQUESTED"
                            # Go back to Beginning
                            continue
                        # QUIT WAY -- ALL STAGES
                        elif MSG_FROM_SUP in ['Q', 'q']:
                            STATE_CTRL = 'QUIT_ST'
                        else:
                            # <<<--- Reply to SUPERVISORIO
                            con.send ("Invalid Command : " +STATE_CTRL)
                            print "...Invalid Command ("+MSG_FROM_SUP+") : " +STATE_CTRL
                            # Go back to Beginning
                            continue
                    #
                    #
                    # ------------- DATA PATH STATE LOGIC --------------
                    #
                    # FSM Activities
                    # Actions in PARALLEL FSM Mealy Way
                    # CONNECTED STATE Actions
                    if STATE_CTRL == 'CONNECTED_ST':
                        # <<<--- Reply to SUPERVISORIO
                        con.send (STATE_CTRL + '\n' + CONNECTED_CMD_STS())
                        print "--> ("+MSG_FROM_SUP+") Go to : "+STATE_CTRL
                    #
                    # CONFIGURED STATE Actions
                    elif STATE_CTRL == 'CONFIGURED_ST':
                        #
                        # Change the RUN File to 1 (CONFIGURE, CONF to FPGA)
                        spilibx.SAVE_DATA_LOG_ANALYSIS(FILE_RUN_STATUS_PATH, '1')
                        #
                        # <<<--- Reply to SUPERVISORIO
                        con.send (STATE_CTRL)
                        print "--> ("+MSG_FROM_SUP+") Go to : "+STATE_CTRL
                    #
                    # READY STATE Actions
                    elif STATE_CTRL == 'READY_ST':
                        # Change the RUN File to 0 (STOP)
                        spilibx.SAVE_DATA_LOG_ANALYSIS(FILE_RUN_STATUS_PATH, '0')
                        #
                        # <<<--- Reply to SUPERVISORIO
                        con.send (STATE_CTRL + '\n' + READY_CMD_STS())
                        print "--> ("+MSG_FROM_SUP+") Go to : "+STATE_CTRL
                    #
                    # RUNNING STATE Actions
                    elif STATE_CTRL == 'RUNNING_ST':
                        #
                        # Change the RUN File to 2 (RUN)
                        spilibx.SAVE_DATA_LOG_ANALYSIS(FILE_RUN_STATUS_PATH, '2')
                        #
                        # <<<--- Reply to SUPERVISORIO
                        run_iddx = spilibx.READ_ONLY_FIRST_LINE(FILE_IDD_RUN_NUMBER_PATH)
                        con.send (STATE_CTRL + "\nRUN ID: " + run_iddx )
                        print "--> ("+MSG_FROM_SUP+") Go to : "+STATE_CTRL
                    # QUIT STATE Actions (Combine with START in PARALLEL)
                    elif STATE_CTRL == 'QUIT_ST':
                        #
                        # Change the RUN File to 0 (STOP)
                        spilibx.SAVE_DATA_LOG_ANALYSIS(FILE_RUN_STATUS_PATH, '0')
                        #
                        # <<<--- Reply to SUPERVISORIO
                        con.send (STATE_CTRL + " --> Clear ALL --> START_ST")
                        print "--> ("+MSG_FROM_SUP+") Go to : " + STATE_CTRL + "---> START_ST"
                        # Next State
                        STATE_CTRL = 'START_ST'
                        print "**** Clear ALL ****"
                    #
                    #
                else:
                    # Reply the Error !
                    # <<<--- Reply to SUPERVISORIO
                    con.send ("Command NOT FOUND: ("+ MSG_FROM_SUP + ") - Current State: " + STATE_CTRL)
                    print "...Command NOT FOUND: ("+MSG_FROM_SUP+")" + " - Current State: " + STATE_CTRL
                #
                
                # ---------------------------------- State Machine ----------------------------------
                
            # Closing Coonection
            print '--- Finishing the Client Connection ...', cliente
            con.close()
        #
    # Basic Exceptions
    except socket.error as errm:
        print "Socket Error: %s" % errm
        time.sleep(5)
        continue
    except TypeError as errm:
        print "Type Error: %s" % errm
        time.sleep(5)
        continue

