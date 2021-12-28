#SceRegMgr (Registry Manager) exports some functions that allow querying the value of system parameters (i.e. sceAppUtilSystemParamGetInt)
#Those functions take as the first argument an integer. It is later on mapped to the proper registry key.
#This process is done using a hardcoded lookup table, that also contains whether the key is readable/writable.
#
#This script will generate a report listing all supported integer values, and the corresponding registry key, along with the access permissions.
#
#HOW TO USE THIS SCRIPT:
#First step is to locate the copy of SceRegMgr you want to analyze.
#Then, naviagate to the sceRegMgrUtilitySetInt function.
#It should look something like this (Decompiler output):
#
#SceInt32 sceRegMgrUtilitySetInt(SceUInt32 keyId, SceInt32* value) {
#   /* ... */
#   iVar3 = 0;
#   iVar1 = FUN_81XXXXXX(&localVar);
#   if (-1 < iVar1) {
#       piVar5 = (int*)&DAT_81XXXXXX; //First important line
#       do {
#           piVar5 = piVar5 + 1; //Second important line
#           if (keyId == *piVar5) {
#               if ((&DAT_81XXXXXX)[iVar3 * 4] == 1) { //Third important line
#                   /* ... */
#                   //Important lines ahead! Doesn't matter if strings aren't the same
#                   sceRegMgrSetKeyIntForDriver(
#                       "/CONFIG/SYSTEM" + (&DAT_81XXXXXX)[iVar3 * 4] * 0xYYY,
#                       "button_assign" + (&DAT_81XXXXXX)[iVar3 * 4] * 0xYY
#                   );
#               }
#           }
#       } while (iVar3 != 0xYY); //Last important line
#   }
#}
#
#On the first important line, you will find the address of the keys table.
#However, if the second important line is present, make sure to add 4 to this address!
#
#On the third important line, you will find the address of the mapping table.
#
#In the parameters to sceRegMgrSetKeyIntForKernel, there should be two strings.
#Double-click on them to get to them in the listing, which shows the addresses.
#The first one is the category strings table address, the second one is the key strings table address.
#
#You should now have the 4 addresses to get the script working.
#If it doesn't seem to work, however, here are a few things you can try:
# - set TABLE_NUM_ELEMS to the value seen on the last important line
# - set CATEGORY_STRING_SIZE to the value used to multiply in the call to sceRegMgrSetKeyInt
# - same thing for KEY_STRING_SIZE
#
#@author CreepNT
#@category Vita
#@keybinding 
#@menupath 
#@toolbar 

#Table item layout
#Byte 0: 1 if allowed to be written
#Byte 1: 1 if allowed to be read
#Byte 2: Index in categories table
#Byte 3: Index in keys table

TABLE_NUM_ELEMS = 0x3F
TABLE_ELEM_SIZE = 4
TABLE_SIZE = TABLE_ELEM_SIZE * TABLE_NUM_ELEMS

CATEGORY_STRING_SIZE = 0x100
KEY_STRING_SIZE = 0x1C

def getString(addr):
	s = ""
	while True:
		byte = getByte(addr)
		addr = addr.add(1)
		if (byte == 0):
			return s
		elif byte > 0:
			s += chr(byte)

mem = currentProgram.getMemory()
memMin = mem.getMinAddress()
memMax = mem.getMaxAddress()
addrFactory = currentProgram.getAddressFactory()

#This is the 
keysTableAddress = askString("Enter keys table address", "Base address of the keys table:")
keysTableAddress = addrFactory.getAddress(keysTableAddress)
if not (memMin <= keysTableAddress <= memMax):
	print("Invalid address for keys table - not in program.")
	exit()

categoryStringsTableAddress = askString("Enter category strings table address", 
	"Base address of the category strings table:")
categoryStringsTableAddress = addrFactory.getAddress(categoryStringsTableAddress)
if not (memMin <= categoryStringsTableAddress <= memMax):
	print("Invalid address for category strings table - not in program.")
	exit()


keyStringsTableAddress = askString("Enter key strings table address", 
	"Base address of the key strings table:")
keyStringsTableAddress = addrFactory.getAddress(keyStringsTableAddress)
if not (memMin <= keyStringsTableAddress <= memMax):
	print("Invalid address for key strings table - not in program.")
	exit()

mappingTableAddress = askString("Enter mapping table address",
	"Base address of the mapping table")
mappingTableAddress = addrFactory.getAddress(mappingTableAddress)
if not (memMin <= mappingTableAddress <= memMax):
	print("Invalid address for mapping table - not in program.")
	exit()

tableBytes = getBytes(mappingTableAddress, TABLE_SIZE)

registryMap = {}
for i in range(TABLE_NUM_ELEMS):
	TABLE_IDX = i * 4
	canBeWritten = tableBytes[TABLE_IDX]
	canBeRead = tableBytes[TABLE_IDX + 1]
	categoryIdx = tableBytes[TABLE_IDX + 2]
	keyIdx = tableBytes[TABLE_IDX + 3]

	keyAddress = keysTableAddress.add(TABLE_IDX)
	key = getInt(keyAddress)

	categoryAddress = categoryStringsTableAddress.add(categoryIdx * CATEGORY_STRING_SIZE)
	category = getString(categoryAddress)

	keyNameAddress = keyStringsTableAddress.add(keyIdx * KEY_STRING_SIZE)
	keyName = getString(keyNameAddress)

	if (category[-1] != "/"): #Add a / to separate
		registryMap[key] = (category + "/" + keyName, canBeRead, canBeWritten)
	else: #There is already a / in the category name - don't add one
		registryMap[key] = (category + keyName, canBeRead, canBeWritten)


ALLOWED = ["No", "Yes"]
for key in registryMap.keys():
	print("Key 0x%X:" % key)
	print("\t- Registry key: %s" % registryMap[key][0])
	print("\t- Readable? %s - Writeable? %s" % (ALLOWED[registryMap[key][1]], ALLOWED[registryMap[key][2]]))
