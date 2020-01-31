/*
 *    Filename: angraNDAQ_Aux.c
 *     Project: Neutrinos Angra
 *     Author:  Fernando Franca, Luis Fernando Gomes, Stefan Wagner
 *     Description: DAQ software - low level auxiliary functions
 *     License: (C) 2015 CBPF - Laboratorio de Sistemas de Deteccao
 *
 * -----------------------------------------------------------------------------*/

#ifndef AUX_FUNCTIONS
#define AUX_FUNCTIONS

#include <fcntl.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

/*!
 *  includes Linux' input/output control system call:
 *  <b>int ioctl(int fd, unsigned long request, ...); </b>
 *
 *  The most common use of ioctl() is to control hardware devices. A ioctl() call takes as parameters:
 *  -# an open <i>file descriptor</i> (to special files)
 *  -# a device-dependent <i>request</i> code number
 *  -# an <i>argument</i>, which is either
 *    - an integer value (possibly unsigned, going to the driver) or
 *    - a pointer to data (going to the driver, coming back from the driver, or both)
 *
 *  An ioctl request (second parameter) has encoded in it whether the argument is an in-parameter or
 *  an out-parameter, as well as the size of the argument in bytes. On success usually zero is returned.
 *  On error -1 is returned and ERRNO is set appropriately.
 *
 *  Particularly, the ioctl() function is used to interact with the VME device to read data from
 *  or write data to it.
 *
 *  More info at <a href="http://man7.org/linux/man-pages/man2/ioctl.2.html">man pages</a> or
 *  <a href="https://en.wikipedia.org/wiki/Ioctl">Wikipedia</a>.
 */
#include <sys/ioctl.h>

#include <termios.h>
#include <time.h>
#include <unistd.h> ///< needed for pread() and pwrite()
#include <stdlib.h>

#include "vmedrv.h"
#include "vmelib.h"
#include "vme_am.h"
#include "vme_error.h"


#define DEBUG    0
#define SPI_DATA 0x600000
#define SPI_STAT 0x700000

#define R	if(DEBUG) printf("Response 0x%02X\n", r)

/*****************************************************************************/

typedef union _TDC_REGISTER
{
	unsigned int word;
	struct { unsigned char byte0, byte1, byte2, byte3; };
} TDC_REGISTER;




/*****************************************************************************/
/*
 * Auxiliary functions
 */

/**
* Debug function to visualize the binary representation of an 8-bit integer number. Many settings
* and controls are encoded in single bits of a char-type variable (i.e. a one-byte number), so
* this function can help to understand what settings and values are passed between the program
* and the hardware.
*/
void printBits(int n)
{
   printf("%i", (n>>7) & 0b1);
   printf("%i", (n>>6) & 0b1);
   printf("%i", (n>>5) & 0b1);
   printf("%i", (n>>4) & 0b1);
   printf("%i", (n>>3) & 0b1);
   printf("%i", (n>>2) & 0b1);
   printf("%i", (n>>1) & 0b1);
   printf("%i", (n>>0) & 0b1);
   printf("\n");
}


/// Control Linux's line buffering (ENABLE or DISABLE)
/// This function is needed so that kbhit() works properly
void linebuffer(int enable)
{
	static struct termios oldt, newt;

	if(enable == 0)
	{
	    tcgetattr(STDIN_FILENO, &oldt);
	    newt = oldt;
	    newt.c_lflag &=~ (ICANON | ECHO);
	    tcsetattr(STDIN_FILENO, TCSANOW, &newt);
	}
	else tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
}

/// Good kbhit() emulation. In order to work properly, line
/// buffering must be DISABLED.
/// This function listens for keyboard input signals and is used
/// to provide an exit option for the program with the 'q' key
int kbhit(void)
{
	struct timeval tv;
	fd_set rdfs;
	tv.tv_sec = 0;
	tv.tv_usec = 0;

	linebuffer(0); /// Switch line buffer OFF. Function defined above

	FD_ZERO(&rdfs);
	FD_SET(STDIN_FILENO, &rdfs);
	select(STDIN_FILENO+1, &rdfs, NULL, NULL, &tv);

	linebuffer(1); /// Switch line buffer ON again.

	return(FD_ISSET(STDIN_FILENO, &rdfs));
}

/// Good getch() emulation. In order to work properly, line
/// buffering must be DISABLED.
int getch(void)
{
	int ch;
	linebuffer(0);  // switch buffer off
	ch = getchar(); // get character from console
	linebuffer(1);  // switch buffer on again
	return(ch);
}


/*****************************************************************************/
/*
 * VMEbus setup
 */

/**
 * DMA read
 * @param add is the source address
 * @param data is the destination address
 * @param pk is the data packet read from the device
 * @param op is the device descriptor (Linux special file)
 */
void readFIFO(int add, unsigned int data[280], vmeDmaPacket_t pk, int op)
{

	// printf("\t readFIFO: \t Before: Add %lu, \tdata[0]: %lu, \tdata[1]: %i\n", add, data[0], data[1]);

	pk.srcAddr = add;			///< DMA source data: source addr
	pk.dstAddr = (unsigned int) data;	///< DMA destination data: dst addr

	ioctl(op, VME_IOCTL_START_DMA, pk);
	/// FIXME: it seems like the VME control works differently from the standard ioctl() calls
	/// described above. VME_IOCTL_START_DMA is a predefined fixed value, but the data packet pk
	/// is flexible and has many attributes (as seen in the readREG() method). It looks like the
	/// device is controlled by the structure of the data packet rather than the request code.

	// printf("\t readFIFO: \t After: Add %lu, \tdata[0]: %lu, \tdata[1]: %i\n", add, data[0], data[1]);

}

/*****************************************************************************/

/**
 * read registers
 * @param add is the source address
 * @param data is the destination address
 * @param op is the device descriptor (Linux special file)
 */
void readREG(int add, unsigned char data, int op)
{
	/// Create vmeDmaPacket_t object and initialize its member variables
	vmeDmaPacket_t pkt;

	pkt.maxPciBlockSize = 16*1024;			///< BUS usage control: PCI bus maximum block size
	pkt.maxVmeBlockSize = 16*1024;			///< BUS usage control: VMEbus maximum block size
	pkt.byteCount = 2;				///< Read size (bytes)

	/// SOURCE CONFIG
	pkt.srcBus = VME_DMA_VME;			///< DMA source data: src bus
	pkt.srcAddrU = 0;				///< DMA source data
	pkt.srcVmeAttr.maxDataWidth = VME_D32;		///< VMEbus transfer attr: maximum data width
	pkt.srcVmeAttr.xferProtocol = VME_BLT;		///< VMEbus transfer attr: transfer protocol
	pkt.srcVmeAttr.addrSpace = VME_A32;		///< VMEbus transfer attr: address space
	pkt.srcVmeAttr.userAccessType = VME_USER;	///< VMEbus transfer attr: user || supervisor access type
	pkt.srcVmeAttr.dataAccessType = VME_DATA;	///< VMEbus transfer attr: data || program access type

	/// DESTINATION CONFIG
	pkt.dstBus = VME_DMA_USER;			///< DMA destination data: dst bus
	pkt.dstAddrU = 0;				///< DMA destination data
	pkt.dstVmeAttr.maxDataWidth = 0;		///< VMEbus transfer attr: maximum data width
	pkt.dstVmeAttr.xferProtocol = 0;		///< VMEbus transfer attr: transfer protocol
	pkt.dstVmeAttr.addrSpace = 0;			///< VMEbus transfer attr: address space
	pkt.dstVmeAttr.userAccessType = 0;		///< VMEbus transfer attr: user || supervisor access type
	pkt.dstVmeAttr.dataAccessType = 0;		///< VMEbus transfer attr: data || program access type

	pkt.srcAddr = add;
	pkt.dstAddr = (unsigned char) data;

	ioctl(op, VME_IOCTL_START_DMA, pkt);		///< send ioctl() call
}

/*****************************************************************************/

/// read VME to see if there was a trigger
void TriggerTest(unsigned int add, unsigned int data[2], vmeDmaPacket_t pk, int op)
{

//	printf("\t TriggerTest: \tadd: %u \tdata[0]: %u\n", add,data[0]);

	pk.srcAddr = add;
	pk.dstAddr = (unsigned int) data;
	ioctl(op, VME_IOCTL_START_DMA, pk);

	//printf("\t TriggerTest: \tdata[0]: %i\n\n", data[0]);

}

/*****************************************************************************/

unsigned char WriteReg(int pda32, unsigned addr, unsigned char byte)
{
	unsigned int data;
	data = byte & 0x000000FF;

	if(pwrite(pda32, &data, sizeof(data), addr)!=sizeof(data)) { perror("ERROR: Cannot write data"); return 0; }
	else return 1;
}

/*****************************************************************************/

unsigned char ReadReg(int pda32, unsigned addr)
{
	unsigned int data;

	if(pread(pda32, &data, sizeof(data), addr)!=sizeof(data)) { perror("ERROR: Cannot read data"); return 0; }
	else return (unsigned char)data;
}

/*****************************************************************************/

unsigned char WriteSSPI(int pda32, int slot, unsigned char data)
{
	unsigned char t=0;

	/// While busy
	while(((ReadReg(pda32, SPI_STAT) & 0x01) == 0x01) && t<10) t++;
	if(!(WriteReg(pda32, SPI_DATA, data))) printf("ERROR: WriteReg Error!\n");
	if(t==10) printf("  SPI busy test TIMED OUT!\n");

	/// While no data
	t=0;
	while(((ReadReg(pda32, SPI_STAT) & 0x02) == 0x00) && t<10) t++;
	if(t==10) printf("  SPI data test TIMED OUT!\n");

	return ReadReg(pda32, SPI_DATA);
}

/*****************************************************************************/

bool WriteCore(int pda32, int slot, unsigned char addr, unsigned char data)
{
	unsigned char temp=0, r=0;

	r = WriteSSPI(pda32, slot, 0xAA); R;	///< Write cmd
	r = WriteSSPI(pda32, slot, addr); R;	///< Addr ph1 - ls nibble (4 bits)
	r = WriteSSPI(pda32, slot, data); R;	///< Addr ph2 - ms nibble (4 bits)
	r = WriteSSPI(pda32, slot, 0xFF); R;	///< Getting response

	if(r == 0xEB) return true;
	else return false;
}

/*****************************************************************************/

unsigned char ReadCore(int pda32, int slot, unsigned char addr)
{
	unsigned char temp=0, r=0;

	r = WriteSSPI(pda32, slot, 0x2A); R;	///< Read cmd
	r = WriteSSPI(pda32, slot, addr); R;	///< Addr ph1 - ls nibble (4 bits)
	r = WriteSSPI(pda32, slot, 0xFF); R;	///< Getting response and it is the register's value

	return r;
}

/*****************************************************************************/

bool TDCWriteReg(int pda32, int slot, unsigned char base_addr, TDC_REGISTER data)
{
	/*!
	 * Sao necessarios 4 registradores (8 bits cada) da FPGA CORE para
	 * armazenar os 28 bits de cada registrador do TDC. A CPU do ROP e um
	 * PowerPC (Motorola) -> Alinhamento dos bytes é BIG ENDIAN. Então,
	 * data.byte0 é o byte MAIS SIGNIFICATIVO.
	 */
	if (WriteCore(pda32, slot, base_addr+0, data.byte3) &&
	    WriteCore(pda32, slot, base_addr+1, data.byte2) &&
	    WriteCore(pda32, slot, base_addr+2, data.byte1) &&
	    WriteCore(pda32, slot, base_addr+3, data.byte0))
	{
	    return(true);
	}
	else return false;
}

#endif

/*****************************************************************************/
