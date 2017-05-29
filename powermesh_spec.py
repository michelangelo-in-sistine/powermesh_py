#!d:\\python27 python2.7
# -*- coding: cp936 -*-

#/******************** (C) COPYRIGHT	2016 ***************************************
#* File Name			 : powermesh_spec.h
#* Author			 : Lv Haifeng
#* Version			 : V 1.6.0
#* Date				 : 02/26/2013
#* Description		 : powermesh协议中定义的数据段,	数据位
#********************************************************************************
#* THE PRESENT FIRMWARE WHICH IS	FOR	GUIDANCE ONLY AIMS AT PROVIDING	CUSTOMERS
#* WITH CODING INFORMATION REGARDING	THEIR PRODECTS IN ORDER	FOR	THEM TO	SAVE TIME.
#* AS A RESULT, BELLING INC.	SHALL NOT BE HELD LIABLE FOR ANY DIRECT,
#* INDIRECT OR CONSEQUENTIAL	DAMAGES	WITH RESPECT TO	ANY	CLAINMS	ARISING	FROM THE
#* CONTENT OF SUCH FIRMWARE AND/OR THE USE MADE BY CUSTOMERS	OF THE CODING
#* INFORMATION CONTAINED	HEREIN IN CONNECTION WITH THEIR	PRODUCTS.
#*******************************************************************************/

#/* Define to prevent recursive inclusion -------------------------------------*/
##ifndef	_POWERMESH_SPEC_H
##define	_POWERMESH_SPEC_H

#/* Includes	------------------------------------------------------------------*/

#/* Firmware	Version	*/
FIRM_VER					= 0x01 #//2015-03-10 update powermesh package definition

#/***************************************************************************************************
#*										SRF	Definition
#*								  SRF: PHPR	+ BODY(2 Bytes)	+ CS
#*								  Use for EBC broadcast	response
#***************************************************************************************************/
#/* SRF数据段绝对位置定义 */
SEC_SRF_PHPR				= 0
SEC_SRF_BODY				= 1
SEC_SRF_CS					= 3

#/* SRF数据段绝对长度定义 */
LEN_SRF_PHPR				= 1
LEN_SRF_BODY				= 2
LEN_SRF_CS					= 3

#/* SRF层对象绝对位置定义 */
SEC_SRF_PPDU				= SEC_SRF_PHPR
SEC_SRF_PSDU				= SEC_SRF_BODY
SEC_SRF_LPDU				= SEC_SRF_BODY
SEC_SRF_LSDU				= SEC_SRF_BODY

#/* 数据段相对位置定义(相对于层)	*/
SEC_SRF_LPDU_BODY			= (LEN_SRF_BODY-SEC_SRF_LPDU)

#/* 层对象开销长度定义 */
LEN_SRF_PPCI_HEAD			= (LEN_SRF_PHPR)
LEN_SRF_PPCI_TAIL			= (LEN_SRF_CS)
LEN_SRF_PPCI				= (LEN_SRF_PPCI_HEAD+LEN_SRF_PPCI_TAIL)

#/***************************************************************************************************
#*								 Non-SRF PHY, DLL Definition
#* |	  PHPR	 |	 LEN   |   CS	|	DEST(6)	  |	  DLCT	 |	 SRC(6)	  |	  LSDU(N)	|	CRC(2)	 |
#*								|<-----------------LPCI-------------->|<---LSDU---->|
#*								|<----------------------------LPDU----------------->|
#*
#* |<---------PPCI-------------->|<-------------------PSDU-------------------------->|<---PPCI--->|
#* |<----------------------------------------PPDU------------------------------------------------>|
#****************************************************************************************************/
#/* Non-SRF Package Definition */
#/* 数据段绝对位置定义 */
SEC_PHPR					= 0
SEC_LENL					= 1			#//SEC_PHPR + LEN_PHPR
SEC_CS						= 2			#//SEC_LENL + LEN_LENL
SEC_DEST					= 3			#//SEC_CS + LEN_CS
SEC_DLCT					= 9			#//SEC_DEST + LEN_DEST
SEC_SRC						= 10			#//SEC_DLCT + LEN_DLCT
SEC_PPDU					= SEC_PHPR
SEC_PSDU					= SEC_DEST
SEC_LPDU					= SEC_PSDU
SEC_LSDU					= 16
SEC_NPDU					= SEC_LSDU
SEC_NSDU					= 19
SEC_MPDU					= SEC_NSDU
SEC_MSDU					= SEC_MPDU + 1
SEC_APDU					= SEC_MSDU


#/* 数据段绝对长度定义 */
LEN_PHPR					= 1
LEN_LENL					= 1
LEN_CS						= 1
LEN_DEST					= 6
LEN_DLCT					= 1
LEN_SRC						= 6
LEN_CRC						= 2
LEN_PIPE_ID					= 2
LEN_PIPE_CONF				= 1

#/* 数据段相对位置定义(相对于层)	*/
SEC_LPDU_DEST				= (SEC_DEST-SEC_LPDU)		#//DEST 相对	LPDU的位置
SEC_LPDU_DLCT				= (SEC_DLCT-SEC_LPDU)		#//DLCT 相对	LPDU的位置
SEC_LPDU_SRC				= (SEC_SRC-SEC_LPDU)		#//SRC 相对 LPDU的位置
SEC_LPDU_LSDU				= (SEC_LSDU-SEC_LPDU)		#//SRC 相对 LPDU的位置
SEC_LPDU_MPDU				= (SEC_MPDU-SEC_LPDU)

#/* 层对象开销长度定义 */
LEN_PPCI_HEAD				= (LEN_PHPR+LEN_LENL+LEN_CS)
LEN_PPCI_TAIL				= (LEN_CRC)
LEN_PPCI					= (LEN_PPCI_HEAD+LEN_PPCI_TAIL)
LEN_LPCI					= (LEN_DEST+LEN_DLCT+LEN_SRC)
LEN_TOTAL_OVERHEAD_BEYOND_LSDU	= (LEN_PPCI+LEN_LPCI)		#//ppdu_len = lsdu_len +	lsdu_overhead
LEN_NPCI					= (LEN_PIPE_ID+LEN_PIPE_CONF)
LEN_MPCI					= 1
LEN_TOTAL_OVERHEAD_BEYOND_NSDU	= (LEN_PPCI+LEN_LPCI+LEN_NPCI)		#//ppdu_len = lsdu_len +	lsdu_overhead



#/* 数据位定义 */
BIT_PHPR_LENH				= 0x80	#// ppdu	length = BIT_PHPR_LENH * 256 + SEC_LENL
BIT_PHPR_SCAN				= 0x08
BIT_PHPR_SRF				= 0x04
BIT_PHY_RCV_FLAG_SCAN		= 0x08
BIT_PHY_RCV_FLAG_SRF		= 0x04

PLC_FLAG_SCAN				= 0x08
PLC_FLAG_SRF				= 0x04
PHY_FLAG_SCAN				= 0x08
PHY_FLAG_SRF				= 0x04
PHY_FLAG_NAV				= 0x84

BIT_DLL_DIAG				= 0x80	#//	bit	in dll_rcv_valid
BIT_DLL_ACK					= 0x40
BIT_DLL_REQ_ACK				= 0x20
BIT_DLL_VALID				= 0x10
BIT_DLL_SCAN				= 0x08
BIT_DLL_SRF					= 0x04
BIT_DLL_IDX					= 0x03

BIT_DLCT_DIAG				= 0x80
BIT_DLCT_ACK				= 0x40
BIT_DLCT_REQ_ACK			= 0x20
BIT_DLCT_IDX				= 0x03

BIT_DLL_SEND_PROP_DIAG		= 0x80	#//[DIAG	ACK	REQ_ACK	EDP	SCAN SRF 0 ACUPDATE]
BIT_DLL_SEND_PROP_ACK		= 0x40
BIT_DLL_SEND_PROP_REQ_ACK	= 0x20
BIT_DLL_SEND_PROP_EDP		= 0x10
BIT_DLL_SEND_PROP_SCAN		= 0x08
BIT_DLL_SEND_PROP_SRF		= 0x04
BIT_DLL_SEND_PROP_ACUPDATE	= 0x01

#/***************************************************************************************************
#*									  EDP/EBC Definition
#****************************************************************************************************/
EXP_DLCT_EDP				= 0xBC		#// EXP_:表达式常数,	EDP: Extended Diagnose Protocol	扩展DLL协议
EXP_EDP_EBC					= 0x40		#// EBC协议是EDP协议的一种

EXP_EDP_EBC_NBF				= 0x00		#// EBC协议包括的四种帧类型(实际是五种, 还有一种b-srf)
EXP_EDP_EBC_NIF				= 0x01
EXP_EDP_EBC_NAF				= 0x02
EXP_EDP_EBC_NCF				= 0x03

SEC_NBF_CONF				= SEC_LSDU+0x00
SEC_NBF_ID					= SEC_LSDU+0x01
SEC_NBF_MASK				= SEC_LSDU+0x02
SEC_NBF_COND				= SEC_LSDU+0x03
SEC_LPDU_NBF_CONF			= SEC_NBF_CONF - SEC_LPDU
SEC_LPDU_NBF_ID				= SEC_NBF_ID -   SEC_LPDU
SEC_LPDU_NBF_MASK			= SEC_NBF_MASK - SEC_LPDU
SEC_LPDU_NBF_COND			= SEC_NBF_COND - SEC_LPDU
SEC_LSDU_NBF_CONF			= SEC_NBF_CONF - SEC_LPDU
SEC_LSDU_NBF_ID				= SEC_NBF_ID -   SEC_LPDU
SEC_LSDU_NBF_MASK			= SEC_NBF_MASK - SEC_LPDU
SEC_LSDU_NBF_COND			= SEC_NBF_COND - SEC_LPDU



SEC_NIF_CONF				= SEC_LSDU+0x00
SEC_NIF_ID					= SEC_LSDU+0x01
SEC_NIF_ID2					= SEC_LSDU+0x02
SEC_LPDU_NIF_CONF			= SEC_NIF_CONF - SEC_LPDU
SEC_LPDU_NIF_ID				= SEC_NIF_ID -   SEC_LPDU
SEC_LPDU_NIF_ID2			= SEC_NIF_ID2	-  SEC_LPDU
SEC_LSDU_NIF_CONF			= SEC_NIF_CONF - SEC_LSDU
SEC_LSDU_NIF_ID				= SEC_NIF_ID -   SEC_LSDU
SEC_LSDU_NIF_ID2			= SEC_NIF_ID2	-  SEC_LSDU


SEC_NAF_CONF				= SEC_LSDU+0x00
SEC_NAF_ID					= SEC_LSDU+0x01
SEC_NAF_ID2					= SEC_LSDU+0x02
SEC_LPDU_NAF_CONF			= SEC_NAF_CONF - SEC_LPDU
SEC_LPDU_NAF_ID				= SEC_NAF_ID -   SEC_LPDU
SEC_LPDU_NAF_ID2			= SEC_NAF_ID2	-  SEC_LPDU
SEC_LSDU_NAF_CONF			= SEC_NAF_CONF - SEC_LSDU
SEC_LSDU_NAF_ID				= SEC_NAF_ID -   SEC_LSDU
SEC_LSDU_NAF_ID2			= SEC_NAF_ID2	-  SEC_LSDU


SEC_NCF_CONF				= SEC_LSDU+0x00
SEC_NCF_ID					= SEC_LSDU+0x01
SEC_NCF_ID2					= SEC_LSDU+0x02
SEC_LPDU_NCF_CONF			= SEC_NCF_CONF - SEC_LPDU
SEC_LPDU_NCF_ID				= SEC_NCF_ID -   SEC_LPDU
SEC_LPDU_NCF_ID2			= SEC_NCF_ID2	-  SEC_LPDU


BIT_NBF_MASK_ACPHASE		= 0x01
BIT_NBF_MASK_SS				= 0x02
BIT_NBF_MASK_SNR			= 0x04
BIT_NBF_MASK_UID			= 0x08
BIT_NBF_MASK_METERID		= 0x10
BIT_NBF_MASK_BUILDID		= 0x20

#/***************************************************************************************************
#*									  PSR Definition
#****************************************************************************************************/
CST_PSR_PROTOCOL			= 0x60

SEC_PSR_ID					= SEC_LSDU+0x00
SEC_PSR_ID2					= SEC_LSDU+0x01
SEC_PSR_CONF				= SEC_LSDU+0x02

SEC_LPDU_PSR_ID				= SEC_PSR_ID - SEC_LPDU
SEC_LPDU_PSR_ID2			= SEC_PSR_ID2	- SEC_LPDU
SEC_LPDU_PSR_CONF			= SEC_PSR_CONF - SEC_LPDU
SEC_LPDU_PSR_NPDU			= SEC_NPDU - SEC_LPDU
SEC_LPDU_PSR_NSDU			= SEC_NSDU - SEC_LPDU

SEC_LSDU_PSR_ID				= SEC_PSR_ID - SEC_LSDU
SEC_LSDU_PSR_ID2			= SEC_PSR_ID2	- SEC_LSDU
SEC_LSDU_PSR_CONF			= SEC_PSR_CONF - SEC_LSDU
SEC_LSDU_PSR_NPDU			= SEC_NPDU - SEC_LSDU
SEC_LSDU_PSR_NSDU			= SEC_NSDU - SEC_LSDU


SEC_NPDU_PSR_ID				= SEC_PSR_ID - SEC_NPDU
SEC_NPDU_PSR_ID2			= SEC_PSR_ID2	- SEC_NPDU
SEC_NPDU_PSR_CONF			= SEC_PSR_CONF - SEC_NPDU
SEC_NPDU_PSR_NSDU			= SEC_NSDU - SEC_NPDU

SEC_NSDU_PSR_ID				= SEC_PSR_ID - SEC_NSDU
SEC_NSDU_PSR_ID2			= SEC_PSR_ID2	- SEC_NSDU
SEC_NSDU_PSR_CONF			= SEC_PSR_CONF - SEC_NSDU

BIT_PSR_SEND_PROP_SETUP		= 0x80
BIT_PSR_SEND_PROP_PATROL	= 0x40
BIT_PSR_SEND_PROP_BIWAY		= 0x20
BIT_PSR_SEND_PROP_SELFHEAL	= 0x10
BIT_PSR_SEND_PROP_UPLINK	= 0x08
BIT_PSR_SEND_PROP_ERROR		= 0x04
BIT_PSR_SEND_PROP_INDEX		= 0x03
BIT_PSR_SEND_PROP_INDEX1	= 0x02
BIT_PSR_SEND_PROP_INDEX0	= 0x01



BIT_PSR_CONF_SETUP			= 0x80		#//This packet is a pipe	setup packet
BIT_PSR_CONF_PATROL			= 0x40		#//This packet is a patrol diagnose packet
BIT_PSR_CONF_BIWAY			= 0x20		#//Link is bi-direction
BIT_PSR_CONF_SELFHEAL		= 0x10		#//Enable self-heal when	ack	communication failed
BIT_PSR_CONF_UPLINK			= 0x08		#//1: uplink(from consignee to pipe setuper), 0:downlink(from setuper to	consignee);
BIT_PSR_CONF_ERROR			= 0x04
BIT_PSR_CONF_INDEX1			= 0x02
BIT_PSR_CONF_INDEX0			= 0x01

BIT_PSR_PIPE_INFO_BIWAY		= 0x8000
BIT_PSR_PIPE_INFO_ENDPOINT	= 0x4000
BIT_PSR_PIPE_INFO_UPLINK	= 0x2000		#//所有被动建立PIPE的节点, PIPE对它永远是UPlink方向,	所有主动发起setup的对象(CC)	PIPE是downlink方向,	此位为0

#/***************************************************************************************************
#*									  DST Definition
#****************************************************************************************************/
CST_DST_PROTOCOL			= 0x10				#//Direct-Scan-TransPort	协议

SEC_DST_CONF				= SEC_LSDU+0x00
SEC_DST_JUMPS				= SEC_LSDU+0x01
SEC_DST_FORW				= SEC_LSDU+0x02
SEC_DST_ACPS				= SEC_LSDU+0x03		#//ACPS,NETWORKID,WINDOW_STAMP为固定的位置
SEC_DST_NETWORK_ID			= SEC_LSDU+0x04
SEC_DST_WINDOW_STAMP		= SEC_LSDU+0x05
SEC_DST_NSDU				= SEC_LSDU+0x06

SEC_NPDU_DST_CONF			= SEC_DST_CONF - SEC_LSDU
SEC_NPDU_DST_JUMPS			= SEC_DST_JUMPS -	SEC_LSDU
SEC_NPDU_DST_FORW			= SEC_DST_FORW - SEC_LSDU
SEC_NPDU_DST_NETWORK_ID		= SEC_DST_NETWORK_ID - SEC_LSDU
SEC_NPDU_DST_WINDOW_STAMP	= SEC_DST_WINDOW_STAMP - SEC_LSDU
SEC_NPDU_DST_NSDU			= SEC_DST_NSDU - SEC_LSDU

SEC_LPDU_DST_CONF			= SEC_DST_CONF - SEC_LPDU
SEC_LPDU_DST_JUMPS			= SEC_DST_JUMPS -	SEC_LPDU
SEC_LPDU_DST_FORW			= SEC_DST_FORW - SEC_LPDU
SEC_LPDU_DST_NETWORK_ID		= SEC_DST_NETWORK_ID - SEC_LPDU
SEC_LPDU_DST_WINDOW_STAMP	= SEC_DST_WINDOW_STAMP - SEC_LPDU
SEC_LPDU_DST_NSDU			= SEC_DST_NSDU - SEC_LPDU

LEN_DST_NPCI				= (6)



BIT_DST_CONF_INDEX			= 0x03
BIT_DST_CONF_UPLINK			= 0x04
BIT_DST_CONF_SEARCH			= 0x08

BIT_DST_FORW_WINDOW			= 0x07
BIT_DST_FORW_WINDOW_DEC		= 0x08
BIT_DST_FORW_ACPS			= 0x10
BIT_DST_FORW_NETWORK		= 0x20
BIT_DST_FORW_MID			= 0x80
BIT_DST_FORW_CONFIG_LOCK	= 0x40		#//2014-11-17 调用CONFIG_DST_FLOODING后将此标志位抬起,app_send后将此位撤销,当此标志位有效时,接收不改变dst config



#/***************************************************************************************************
# *									  DST Definition
# * 2016-07-16 PTP协议, 最简单的点对点直接发送, 节省DST的代码开销, 以及传输开销
# ****************************************************************************************************/
CST_PTP_PROTOCOL			= 0xF0		#//Peer To Peer 协议
LEN_PTP_NPCI				= (1)

SEC_PTP_NSDU				= SEC_LSDU+LEN_PTP_NPCI
SEC_PTP_APDU				= SEC_LSDU+LEN_PTP_NPCI+LEN_MPCI


SEC_LPDU_PTP_NSDU			= SEC_PTP_NSDU - SEC_LPDU
SEC_LPDU_PTP_APDU			= SEC_PTP_APDU - SEC_LPDU

#/***************************************************************************************************
#*									  Mgnt Definition
#****************************************************************************************************/
#/* Management Cmd Definition */
EXP_MGNT_PING				= 0x00
EXP_MGNT_DIAG				= 0x01
EXP_MGNT_EBC_BROADCAST		= 0x02
EXP_MGNT_EBC_IDENTIFY		= 0x03
EXP_MGNT_EBC_ACQUIRE		= 0x04
EXP_MGNT_SET_BUILD_ID		= 0x05


SEC_NPDU_MPDU				= SEC_MPDU-SEC_NPDU
SEC_NPDU_MSDU				= SEC_MSDU-SEC_NPDU
SEC_NPDU_APDU				= SEC_APDU-SEC_NPDU

SEC_MPDU_MSDU				= SEC_MSDU-SEC_MPDU

