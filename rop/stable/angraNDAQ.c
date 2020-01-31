/*    Filename: angraNDAQ.c
 *     Project: Neutrinos Angra
 * Description: Data acquisition software for the Neutrinos Angra reactor
 *              antineutrino experiment
 *     License: Apache 2.0 
 * 
 *     2018 CBPF - Centro Brasileiro de Pesquisas Fisicas
 *     Laboratorio de Sistemas de Deteccao (LSD)
 */
#define VERSION "2.0.0" ///< First production version

#include <fcntl.h>      ///< file control; needed to open the device descriptor file
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>  ///< input/output control; system calls needed to access the hardware
#include <sys/types.h>
#include <sys/socket.h> ///< for TCP/IP connections with client
#include <errno.h>      ///< for error handling; needed for nonblocking TCP/IP reads
#include <netdb.h>                                                                                                                                                                              
                                                                                                                                                                                                
#include <termios.h>                                                                                                                                                                            
#include <time.h>                                                                                                                                                                               
#include <unistd.h>                                                                                                                                                                             
#include <stdlib.h>                                                                                                                                                                             

#include <unistd.h> ///< to process command line arguments

#include "vmedrv.h"
#include "vmelib.h"
#include "vme_am.h"
#include "vme_error.h"

#include "angraNDAQ.h" ///< low level functions

//Redis
#include <hiredis.h>

//------------------------------------------------------------------------------------------------

#define ADC    100   ///< defines the number of ADC samples (has to be an even number!)
#define WORD   ADC/2 ///< ADC word
#define OTHERS 7

//TDC
#define CONTINUOUS 0
int verbose=0;
///###############################################################################################################


int initNDAQ(int pda32, int slot)
{
        vmeOutWindowCfg_t SlotWin =  {slot,1,0,0,0,VME_MAX_SIZE,0,0x8000000*slot,0,0,0,0,VME_SSTNONE,VME_A32,VME_D32,VME_SCT,VME_USER,VME_DATA,0};

        if (vme_set_outbound(pda32, &SlotWin))
        {
            vme_perror("Cannot configure VME window for A32 D32");
            vme_show_outbound(2, &SlotWin);
        }

        unsigned int datapkt;
        if( pread(pda32, &datapkt, sizeof(datapkt), SPI_STAT)!=sizeof(datapkt) )        {
                return 0;
        }


        // VME FPGA Reset
        if (!WriteReg(pda32,0xa00000, 0x55) && verbose>2) printf("  Can't Reset VME FPGA!\n");

        if (WriteCore(pda32, slot, 0xAA, 0x55) && verbose>2) printf("  General Reset    - Ok!\n"); ///< gereral reset
        if (WriteCore(pda32, slot, 0x87, 0x0F) && verbose>2) printf("  ADC Power up     - Ok!\n"); ///< ADC Power Up


        if (WriteCore(pda32, slot, 0xF3, 0x01) && verbose>2) printf("  TDC Reset Enable - Ok!\n"); ///< takes at least 200ns
        if (WriteCore(pda32, slot, 0xF3, 0x00) && verbose>2) printf("  TDC Reset Clear  - Ok!\n"); ///< from the previous instruction to this one more than 200ns pass


        // Disabling the four STOP groups for the configuration of the TDC
        if (WriteCore(pda32, slot, 0xF2, 0x0F)  && verbose>2) printf("TDC STOPs Disable  - Ok!\n");


        TDC_REGISTER tdc_reg;

        if (CONTINUOUS) 
        {
                // TDC REGISTER 0
                tdc_reg.word = 0x007FC81;
                if (TDCWriteReg(pda32, slot, 0xC0, tdc_reg) && verbose>2) printf("  TDC Reg 0        - Ok!\n");
                // TDC REGISTER 1
                tdc_reg.word = 0x0000000;
                if (TDCWriteReg(pda32, slot, 0xC4, tdc_reg) && verbose>2) printf("  TDC Reg 1        - Ok!\n");
                // TDC REGISTER 2
                tdc_reg.word = 0x0000002;
                if (TDCWriteReg(pda32, slot, 0xC8, tdc_reg) && verbose>2) printf("  TDC Reg 2        - Ok!\n");
                // TDC REGISTER 3
                tdc_reg.word = 0x0000000;
                if (TDCWriteReg(pda32, slot, 0xCC, tdc_reg) && verbose>2) printf("  TDC Reg 3        - Ok!\n");
                // TDC REGISTER 4
                tdc_reg.word = 0x2000027;
                if (TDCWriteReg(pda32, slot, 0xD0, tdc_reg) && verbose>2) printf("  TDC Reg 4        - Ok!\n");
                // TDC REGISTER 5
                tdc_reg.word = 0x00004DA;
                if (TDCWriteReg(pda32, slot, 0xD4, tdc_reg) && verbose>2) printf("  TDC Reg 5        - Ok!\n"); //0x1600000
                // TDC REGISTER 6
                tdc_reg.word = 0x0000000;
                if (TDCWriteReg(pda32, slot, 0xD8, tdc_reg) && verbose>2) printf("  TDC Reg 6        - Ok!\n");
                // TDC REGISTER 7
                tdc_reg.word = 0x0281FB4;
                if (TDCWriteReg(pda32, slot, 0xDC, tdc_reg) && verbose>2) printf("  TDC Reg 7        - Ok!\n"); // 0x281FBC=94.9668ps--0x0281F94=100.100ps--0x0281F64=148.15ps


                // TDC REGISTER 11
                tdc_reg.word = 0x7FF0000;
                if (TDCWriteReg(pda32, slot, 0xE0, tdc_reg) && verbose>2) printf("  TDC Reg 11       - Ok!\n");
                // TDC REGISTER 12
                tdc_reg.word = 0x4000000;
                if (TDCWriteReg(pda32, slot, 0xE4, tdc_reg) && verbose>2) printf("  TDC Reg 12       - Ok!\n");

                // No register 13 ? superstition?

                // TDC REGISTER 14
                tdc_reg.word = 0x0000000;
                if (TDCWriteReg(pda32, slot, 0xE8, tdc_reg) && verbose>2) printf("  TDC Reg 14       - Ok!\n");

                // ---------------------------------

                // TDC REGISTER MASTER RESET
                tdc_reg.word = 0x6400027;
                if (TDCWriteReg(pda32, slot, 0xEC, tdc_reg) && verbose>2) printf("  TDC Reg Master Reset     - Ok!\n");

                // TDC Latch Config Enable and Readout Mode
                if (WriteCore(pda32, slot, 0xF0, 0x11) && verbose>2) printf("  TDC Latch Config Enable  - Ok!\n");

                // TDC Latch Config Disable and keep Readout Mode
                if (WriteCore(pda32, slot, 0xF0, 0x10) && verbose>2) printf("  TDC Latch Config Disable - Ok!\n");
        }
        else
        {
                // TDC REGISTER 0
                tdc_reg.word = 0x007FC81;
                if (TDCWriteReg(pda32, slot, 0xC0, tdc_reg) && verbose>2) printf("  TDC Reg 0        - Ok!\n");
                // TDC REGISTER 1
                tdc_reg.word = 0x0000000;
                if (TDCWriteReg(pda32, slot, 0xC4, tdc_reg) && verbose>2) printf("  TDC Reg 1        - Ok!\n");
                // TDC REGISTER 2
                tdc_reg.word = 0x0000002;
                if (TDCWriteReg(pda32, slot, 0xC8, tdc_reg) && verbose>2) printf("  TDC Reg 2        - Ok!\n");
                // TDC REGISTER 3
                tdc_reg.word = 0x0000000;
                if (TDCWriteReg(pda32, slot, 0xCC, tdc_reg) && verbose>2) printf("  TDC Reg 3        - Ok!\n");
                // TDC REGISTER 4
                tdc_reg.word = 0x6000000;
                if (TDCWriteReg(pda32, slot, 0xD0, tdc_reg) && verbose>2) printf("  TDC Reg 4        - Ok!\n");
                // TDC REGISTER 5
                tdc_reg.word = 0x0E00400;
                if (TDCWriteReg(pda32, slot, 0xD4, tdc_reg) && verbose>2) printf("  TDC Reg 5        - Ok!\n"); //0x1600000
                // TDC REGISTER 6
                tdc_reg.word = 0x0000000;
                if (TDCWriteReg(pda32, slot, 0xD8, tdc_reg) && verbose>2) printf("  TDC Reg 6        - Ok!\n");
                // TDC REGISTER 7
                tdc_reg.word = 0x0281FB4;
                if (TDCWriteReg(pda32, slot, 0xDC, tdc_reg) && verbose>2) printf("  TDC Reg 7        - Ok!\n"); // 0x281FBC=94.9668ps--0x0281F94=100.100ps--0x0281F64=148.15ps

                // No registers 8-10 ?

                // TDC REGISTER 11
                tdc_reg.word = 0x3FF0000;
                if (TDCWriteReg(pda32, slot, 0xE0, tdc_reg) && verbose>2) printf("  TDC Reg 11       - Ok!\n");
                // TDC REGISTER 12
                tdc_reg.word = 0x0800000;
                if (TDCWriteReg(pda32, slot, 0xE4, tdc_reg) && verbose>2) printf("  TDC Reg 12       - Ok!\n");

                // No register 13 ? superstition?

                // TDC REGISTER 14
                tdc_reg.word = 0x0000000;
                if (TDCWriteReg(pda32, slot, 0xE8, tdc_reg) && verbose>2) printf("  TDC Reg 14       - Ok!\n");

                // ---------------------------------

                // TDC REGISTER MASTER RESET
                tdc_reg.word = 0x6400000;
                if (TDCWriteReg(pda32, slot, 0xEC, tdc_reg) && verbose>2) printf("  TDC Reg Master Reset - Ok!\n");

                /**
                 * O Registrador abaixo (@0xF0) tem duas funcoes:
                 *
                 * 1 - O Bit 0 (menos significativo) quando ativo (1) faz o
                 * 'latch' dos valores de configuracao de TDC acima.
                 * Este Bit 0 deve ser desligado manualmente.
                 *
                 * 2 - O Bit 7 (mais significativo) escolhe o modo da maquina
                 * de estado que faz a leitura do TDC:
                 * - Bit 7 = '0' -> Modo de leitura SINGLE.
                 * - Bit 7 = '1' -> Modo de leitura CONTINUOUS.
                 */

                //TDC Latch Config Enable and Readout Mode
                if (WriteCore(pda32, slot, 0xF0, 0x01) && verbose>2) printf("  TDC Latch Config Enable - Ok!\n");

                //TDC Latch Config Disable and keep Readout Mode
                if (WriteCore(pda32, slot, 0xF0, 0x00) && verbose>2) printf("  TDC Latch Config Disable - Ok!\n");
        }

        /*
         * Confirmacao do TDC Latch, acessado @0xF1:
         * Se o valor retornado for 0x01, indica que a maq. de configuracao
         * do TDC rodou normalmente.
         */
        unsigned char response;
        if ((response = ReadCore(pda32, slot, 0xF1))!=0x01 && verbose>2) printf("  TDC Latch Config FAILED! - response: 0x%02X!\n", response);

        // TDC STOPs Disable e START Disable
        // Habilitando os 4 grupos de STOPs apos a configuracao do TDC
        if (WriteCore(pda32, slot, 0xF2, 0x00) && verbose>2) printf("  TDC STOPs Enable - Ok!\n");

        // DataBuilder FIFO 1: (LSB) MightyCounter -> LVDS -> Timebase -> ADC -> TDC -> Counter1 -> BusyFlag
  if (WriteCore(pda32, slot, 0x41, 0x7F) && verbose>2) printf("  DataBuilder FIFO 1 - Ok!\n");
        // DataBuilder FIFO 2: (LSB) MightyCounter -> LVDS -> Timebase -> ADC -> TDC -> Counter1 -> BusyFlag (1101 -> D)
        if (WriteCore(pda32, slot, 0x42, 0x7F) && verbose>2) printf("  DataBuilder FIFO 2 - Ok!\n");
        // DataBuilder FIFO 3: (LSB) MightyCounter -> LVDS -> Timebase -> ADC -> TDC -> Counter1 -> BusyFlag (1101 -> D)
        if (WriteCore(pda32, slot, 0x43, 0x7F) && verbose>2) printf("  DataBuilder FIFO 3 - Ok!\n");
        // DataBuilder FIFO 4: (LSB) MightyCounter -> LVDS -> Timebase -> ADC -> TDC -> Counter1 -> BusyFlag (1101 -> D)
        if (WriteCore(pda32, slot, 0x44, 0x7F) && verbose>2) printf("  DataBuilder FIFO 4 - Ok!\n");
        // Number of ADC Samples + 1 (1D = 29 -> 30 Samples) 0x63=100
        if (WriteCore(pda32, slot, 0x81, ADC-1) && verbose>2) printf("  Configuring number of ADC samples - Ok!\n");
        // ACQ Reset Enable
        if (WriteCore(pda32, slot, 0x89, 0x01) && verbose>2) printf("  ACQ Reset Enable - Ok!\n");
        // ACQ Reset Clear
        if (WriteCore(pda32, slot, 0x89, 0x00) && verbose>2) printf("  ACQ Reset Clear - Ok!\n");
        // Flags Reset Clear
        if (WriteCore(pda32, slot, 0x89, 0x02) && verbose>2) printf("  Flags Reset Clear - Ok!\n");
        // ACQ Reset Clear
        if (WriteCore(pda32, slot, 0x89, 0x00) && verbose>2) printf("  ACQ Reset Clear - Ok!\n");
        // DataBuilder Enable
        if (WriteCore(pda32, slot, 0x40, 0x01) && verbose>2) printf("  DataBuilder Enable - Ok!\n");
        // Hardware Enable: (LSB) TimeBase -> Counter -> ETrigger -> iTrigger -> ADC -> DualTrigger => Single Trigger!! -> Angra Version
        if (WriteCore(pda32, slot, 0x80, 0x17) && verbose>2) printf("  Hardware Enable - Ok!\n");
        // Word Mode: '0' for 8 bits, '1' for 10 bits
        if (WriteCore(pda32, slot, 0x82, 0x00) && verbose>2) printf("  FADC bits selector - Ok!\n");

        if (WriteCore(pda32, slot, 0x83, 0x02) && verbose>2) printf("  8 bits range selector - Ok!\n");

        // Flags Reset Clear
        if (WriteCore(pda32, slot, 0x89, 0x02) && verbose>2) printf("  Flags Reset Clear - Ok!\n");
        // ACQ Reset Clear
        if (WriteCore(pda32, slot, 0x89, 0x00) && verbose>2) printf("  ACQ Reset Clear - Ok!\n");

        unsigned int ndaq = 0;
        if (pread(pda32, &ndaq, sizeof(ndaq),0xB00000)!=sizeof(ndaq) && verbose>0) printf("Can't Read NDAQ Number!\n");

        unsigned int data = 0; ///< returns VME FPGA firmware version
        if (pread(pda32, &data, sizeof(data),0x900000)!=sizeof(data) && verbose>0) printf("Can't Read VME Firmware Data!\n");

        unsigned char r = 0;
        r = ReadCore(pda32, slot, 0x28); ///< returns Core FPGA firmware version

        if(verbose>0) printf("NDAQ %d, slot %d: VME FPGA Firmware v%d, Core FPGA Firmware v%d.\n", ndaq, slot, data, r);

        return ndaq;
}


int readNDAQ(int fd, int slot, int cardn, int flag, int buffer[])
{
        int header12[3] = {0};
        int header34[3] = {0};
        int header56[3] = {0};
        int header78[3] = {0};
        unsigned int adc12[WORD]  = {0};
        unsigned int adc34[WORD]  = {0};//WORD
        unsigned int adc56[WORD]  = {0};
        unsigned int adc78[WORD]  = {0};
        unsigned int trigger0[2] = {0};
        flag = 0;
        
        vmeDmaPacket_t header;
        memset(&header, 0, sizeof(header));

        header.maxPciBlockSize = 16*1024;
        header.maxVmeBlockSize = 16*1024;
        header.byteCount = 3*4; ///< read size (bytes)
        header.srcBus = VME_DMA_VME;
        header.srcAddrU = 0;
        header.srcVmeAttr.maxDataWidth = VME_D32;
        header.srcVmeAttr.xferProtocol = VME_BLT;
        header.srcVmeAttr.addrSpace = VME_A32;
        header.srcVmeAttr.userAccessType = VME_USER;
        header.srcVmeAttr.dataAccessType = VME_DATA;
        header.dstBus = VME_DMA_USER;
        header.dstAddrU = 0;
        header.dstVmeAttr.maxDataWidth = 0;
        header.dstVmeAttr.addrSpace = 0;
        header.dstVmeAttr.userAccessType = 0;
        header.dstVmeAttr.dataAccessType = 0;
        header.dstVmeAttr.xferProtocol = 0;


        vmeDmaPacket_t pkt;
        memset(&pkt, 0, sizeof(pkt));

        pkt.maxPciBlockSize = 16*1024;
        pkt.maxVmeBlockSize = 16*1024;
        pkt.byteCount = (WORD + OTHERS - 3) * 4; 
        pkt.srcBus = VME_DMA_VME;
        pkt.srcAddrU = 0;
        pkt.srcVmeAttr.maxDataWidth = VME_D32;
        pkt.srcVmeAttr.xferProtocol = VME_BLT;
        pkt.srcVmeAttr.addrSpace = VME_A32;
        pkt.srcVmeAttr.userAccessType = VME_USER;
        pkt.srcVmeAttr.dataAccessType = VME_DATA;
        pkt.dstBus = VME_DMA_USER;
        pkt.dstAddrU = 0;
        pkt.dstVmeAttr.maxDataWidth = 0;
        pkt.dstVmeAttr.addrSpace = 0;
        pkt.dstVmeAttr.userAccessType = 0;
        pkt.dstVmeAttr.dataAccessType = 0;
        pkt.dstVmeAttr.xferProtocol = 0;


        vmeDmaPacket_t TriggerReg; ///< used to check for the trigger
        memset(&TriggerReg, 0, sizeof(TriggerReg));

        TriggerReg.maxPciBlockSize = 16*1024;
        TriggerReg.maxVmeBlockSize = 16*1024;
        TriggerReg.byteCount = 4; ///< read size (bytes)
        TriggerReg.srcBus = VME_DMA_VME;
        TriggerReg.srcAddrU = 0;
        TriggerReg.srcVmeAttr.maxDataWidth = VME_D32;
        TriggerReg.srcVmeAttr.xferProtocol = VME_BLT;
        TriggerReg.srcVmeAttr.addrSpace = VME_A32;
        TriggerReg.srcVmeAttr.userAccessType = VME_USER;
        TriggerReg.srcVmeAttr.dataAccessType = VME_DATA;
        TriggerReg.dstBus = VME_DMA_USER;
        TriggerReg.dstAddrU = 0;
        TriggerReg.dstVmeAttr.maxDataWidth = 0;
        TriggerReg.dstVmeAttr.addrSpace = 0;
        TriggerReg.dstVmeAttr.userAccessType = 0;
        TriggerReg.dstVmeAttr.dataAccessType = 0;
        TriggerReg.dstVmeAttr.xferProtocol = 0;


        TriggerTest(0x8000000*slot+0x500000, trigger0, TriggerReg, fd);

        //-----------------------------------------------------

        /// Test if any one of the above bits is set
        if ((trigger0[0]&16) > 0) printf("NDAQ Slot %d - catastrophic failure: Overflow FIFOs IDT \n", slot); 
        if ((trigger0[0]&32) > 0) printf("NDAQ Slot %d - catastrophic failure: Overflow FIFOs ADC \n", slot); 
        if ((trigger0[0]&64) > 0) printf("NDAQ Slot %d - catastrophic failure: Overflow FIFOs TDC \n", slot); 
        //if ((trigger0[0]&128) > 0) printf("NDAQ Slot %d - catastrophic failure: PLL non-locked \nTrigger Flag: %x \n", slot, trigger0[0]); 
        
        if ((trigger0[0]&16)||(trigger0[0]&32)||(trigger0[0]&64)) flag = 1;
            
        if ((trigger0[0]&15)==15) 
        {
            readFIFO(0x8000000*slot+0x100000, header12, header, fd); 
            readFIFO(0x8000000*slot+0x200000, header34, header, fd);
            readFIFO(0x8000000*slot+0x300000, header56, header, fd);
            readFIFO(0x8000000*slot+0x400000, header78, header, fd);
            buffer[0]=slot;
            buffer[1]=cardn;
            buffer[2]=trigger0[0];
            memcpy(&buffer[3], header12, sizeof(header12));
            memcpy(&buffer[6], header34, sizeof(header34));
            memcpy(&buffer[9], header56, sizeof(header56));
            memcpy(&buffer[12], header78, sizeof(header78));

            if ( (((header12[1]>>30)&1) && !((header12[1]>>31)&1)) &&
                 (((header34[1]>>30)&1) && !((header34[1]>>31)&1)) &&
                 (((header56[1]>>30)&1) && !((header56[1]>>31)&1)) &&
                 (((header78[1]>>30)&1) && !((header78[1]>>31)&1)) )
            {

                readFIFO(0x8000000*slot+0x100000, adc12, pkt, fd);
                readFIFO(0x8000000*slot+0x200000, adc34, pkt, fd);
                readFIFO(0x8000000*slot+0x300000, adc56, pkt, fd);
                readFIFO(0x8000000*slot+0x400000, adc78, pkt, fd);
                
                memcpy(&buffer[15], adc12, sizeof(adc12));
                memcpy(&buffer[15+WORD], adc34, sizeof(adc34));
                memcpy(&buffer[15+2*WORD], adc56, sizeof(adc56));
                memcpy(&buffer[15+3*WORD], adc78, sizeof(adc78));
            }
            
            return 1;
        }

        else return 0;
}



///###############################################################################################################


void SendData(int buffer0[],int buffer1[],int buffer2[],int buffer3[],int buffer4[],redisContext *c,redisReply *reply)
{
    int send_buffer[5*(4*WORD+12+3)]={0};
    memcpy(&send_buffer, buffer0, 4*(4*WORD+12+3));
    memcpy(&send_buffer[(4*WORD+12+3)], buffer1, 4*(4*WORD+12+3));
    memcpy(&send_buffer[2*(4*WORD+12+3)], buffer2, 4*(4*WORD+12+3));
    memcpy(&send_buffer[3*(4*WORD+12+3)], buffer3, 4*(4*WORD+12+3));
    memcpy(&send_buffer[4*(4*WORD+12+3)], buffer4, 4*(4*WORD+12+3));
    int j=0;
    reply = redisCommand(c,"LPUSH queueEvents1 %b", send_buffer, 
sizeof(send_buffer));
    freeReplyObject(reply);
}

int main()
{
    vmeOutWindowCfg_t window09; 
    int fd = open("/dev/vme_dma0", 0); 
    if(fd == -1) printf("ERROR: Cannot open VME device file");

    // First the single access
    int pda32 = vme_open(); 
    if(pda32 == -1) printf("ERROR: Cannot open 32bits VME path");

    // Initialize NDAQ and automatically check slots for cards
    int NdaqNum[32] = {0}; 
    int NdaqSlot[32] = {0};
    int i = 0;
    int ncards = 0;
    int ndaqn = 0;
    int buffer0[(4*WORD+12+3)] = {0}; //WORD+12+3
    int buffer1[(4*WORD+12+3)] = {0};
    int buffer2[(4*WORD+12+3)] = {0};
    int buffer3[(4*WORD+12+3)] = {0};
    int buffer4[(4*WORD+12+3)] = {0};
    int flag[5] = {0};
    int trigger[5] = {0};
    
    //Redis
    redisContext *c;
    redisReply *reply;
    const char *hostname = "192.168.136.1";
    int port = 6379;
    struct timeval timeout = { 1, 500000 }; // 1.5 seconds
    c = redisConnectWithTimeout(hostname, port, timeout);
    if (c == NULL || c->err) {
        if (c) {
            printf("Connection error: %s\n", c->errstr);
            redisFree(c);
        } else {
            printf("Connection error: can't allocate redis context\n");
        }
        exit(1);
    }
    
    for(i=2; i<30; i++) {
                            ndaqn = initNDAQ(pda32, i);
                            if(ndaqn>0) {
                                        NdaqNum[ncards] = ndaqn;
                                        NdaqSlot[ncards] = i;
                                        ncards++;
                                        printf("NDAQ: %d on Slot: %d\n",ndaqn,i);
                                        ndaqn = 0;
                                        }
                        }
    //printf("NDAQ  response: %d\n",readNDAQ(fd, NdaqSlot[0], NdaqNum[0], flag[0], buffer0));
    i = 0;
    //NdaqSlot[0] = 6;
    //NdaqNum[0] = 15;
    //NdaqSlot[1] = 10;
    //NdaqNum[1] = 7;
    //NdaqSlot[2] = 12;
    //NdaqNum[2] = 7;
    //NdaqSlot[3] = 14;
    //NdaqNum[3] = 20;

    //printf("Slots: %d , %d , %d , %d\n", NdaqNum[0],NdaqNum[1],NdaqNum[2],NdaqNum[3]);
    time_t elapsed_time;
    time_t unix_time = time(NULL);
    while((flag[0]+flag[1]+flag[2]+flag[3])==0){
      while(readNDAQ(fd, NdaqSlot[0], NdaqNum[0], flag[0], buffer0)==0) usleep(1);
      while(readNDAQ(fd, NdaqSlot[1], NdaqNum[1], flag[1], buffer1)==0) usleep(1);
      while(readNDAQ(fd, NdaqSlot[3], NdaqNum[3], flag[3], buffer3)==0) usleep(1);
      while(readNDAQ(fd, NdaqSlot[2], NdaqNum[2], flag[2], buffer2)==0) usleep(1);
      while(readNDAQ(fd, NdaqSlot[4], NdaqNum[4], flag[4], buffer4)==0) usleep(1);
      SendData(buffer0,buffer1,buffer2,buffer3,buffer4,c,reply);
      //freeReplyObject(reply);
      //for(i=0; i<(4*WORD+12+3); i++) printf("%d ",buffer0[i]);
      //usleep(1);
      //i++;
      //if(i==2000000) break;
      if ((time(NULL) - unix_time) >= 15*60) break;
    }
    //for(i=0; i<(4*WORD+12+3); i++) printf("%d ",buffer0[i]);
    return 0;
}

