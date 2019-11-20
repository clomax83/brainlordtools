__author__ = "Roberto Fontanarosa"
__license__ = "GPLv2"
__version__ = ""
__maintainer__ = "Roberto Fontanarosa"
__email__ = "robertofontanarosa@gmail.com"

import sys, os, struct, sqlite3
from collections import OrderedDict

from _rhtools.utils import *
from _rhtools.Table2 import Table

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--crc32check', action='store_true', default=False, help='Execute CRC32CHECK')
parser.add_argument('--dump', action='store_true', default=False, help='Execute DUMP')
parser.add_argument('--insert', action='store_true', default=False, help='Execute INSERTER')
parser.add_argument('--mte_finder', action='store_true', default=False, help='Find MTE')
parser.add_argument('--mte_optimizer', action='store_true', default=False, help='Optimize MTE')
parser.add_argument('-s', '--source', action='store', dest='source_file', required=True, help='Original filename')
parser.add_argument('-d', '--dest',  action='store', dest='dest_file', required=True, help='Destination filename')
parser.add_argument('-t1', '--table1', action='store', dest='table1', required=True, help='Original table filename')
parser.add_argument('-t2', '--table2', action='store', dest='table2', required=True, help='Modified table filename')
parser.add_argument('-t3', '--table3', action='store', dest='table3', required=False, help='Base original table without')
parser.add_argument('-db', '--database',  action='store', dest='database_file', required=True, help='DB filename')
parser.add_argument('-u', '--user', action='store', dest='user', required=True, help='')
args = parser.parse_args()

execute_crc32check = args.crc32check
execute_dump = args.dump
execute_inserter = args.insert
execute_mtefinder = args.mte_finder
execute_mteoptimizer = args.mte_optimizer
filename = args.source_file
filename2 = args.dest_file
tablename = args.table1
tablename2 = args.table2
tablename3 = args.table3
db = args.database_file
user_name = args.user
dump_path = 'ys4/dump/'

SNES_HEADER_SIZE = 0x200
SNES_BANK_SIZE = 0x8000

#CRC32_ORIGINAL = 'CA7B4DB9'
CRC32 = '27577EC8'

DICT1_POINTER_BLOCK_START = 0x85000
#DICT1_POINTER_BLOCK_END = DICT1_POINTER_BLOCK_LIMIT = 0x85839
DICT1_POINTER_BLOCK_END = DICT1_POINTER_BLOCK_LIMIT = 0x85fff
DICT1_BLOCK_START = 0x86000
#DICT1_BLOCK_END = DICT1_BLOCK_LIMIT = 0x87f19
DICT1_BLOCK_END = DICT1_BLOCK_LIMIT = 0x87fff

POINTER_BLOCK1_START = 0x79203
POINTER_BLOCK1_END = POINTER_BLOCK1_LIMIT = 0x7a2ee
POINTER_ITEM_BLOCK_START = 0x4e15f
POINTER_ITEM_BLOCK_END = POINTER_ITEM_BLOCK_LIMIT = 0x4e1e4
POINTER_PLACES_BLOCK_START = 0x4eca0
POINTER_PLACES_BLOCK_END = POINTER_PLACES_BLOCK_LIMIT = 0x4efa9

TEXT_BLOCK1_START = 0x60000
TEXT_BLOCK1_END = TEXT_BLOCK1_LIMIT = 0x67fff
TEXT_BLOCK2_START = 0x68000
TEXT_BLOCK2_END = TEXT_BLOCK2_LIMIT = 0x6ffff
TEXT_BLOCK3_START = 0x71100
TEXT_BLOCK3_END = TEXT_BLOCK3_LIMIT = 0x7296e
TEXT_BLOCK4_START = 0x7a400
TEXT_BLOCK4_END = TEXT_BLOCK4_LIMIT = 0x7fffa
TEXT_BLOCK5_START = 0xc62c0
TEXT_BLOCK5_END = TEXT_BLOCK5_LIMIT = 0xc7fff
TEXT_BLOCK6_START = 0x4efab
TEXT_BLOCK6_END = TEXT_BLOCK6_LIMIT = 0x4f230
ITEM_BLOCK_START = 0x4e1e5
#ITEM_BLOCK_END = ITEM_BLOCK_LIMIT = 0x4e4b3
ITEM_BLOCK_END = ITEM_BLOCK_LIMIT = 0x4e4db
PLACES_BLOCK_START = 0x4f23b
#PLACES_BLOCK_END = PLACES_BLOCK_LIMIT = 0x4fba3
PLACES_BLOCK_END = PLACES_BLOCK_LIMIT = 0x4fff0

table = Table(tablename)
table2 = Table(tablename2)

def ys4BlockResolver(address):
	""" """
	block = 0
	if address >= TEXT_BLOCK1_START and address <= TEXT_BLOCK1_LIMIT:
		block = 1
	if address >= TEXT_BLOCK2_START and address <= TEXT_BLOCK2_LIMIT:
		block = 2
	if address >= TEXT_BLOCK3_START and address <= TEXT_BLOCK3_LIMIT:
		block = 3
	if address >= TEXT_BLOCK4_START and address <= TEXT_BLOCK4_LIMIT:
		block = 4
	if address >= TEXT_BLOCK5_START and address <= TEXT_BLOCK5_LIMIT:
		block = 5
	if address >= TEXT_BLOCK6_START and address <= TEXT_BLOCK6_LIMIT:
		block = 6
	return block

def ys4BlockLimitsResolver(block):
	""" """
	blockLimits = (0, 0)
	if block == 1:
		blockLimits = (TEXT_BLOCK1_START, TEXT_BLOCK1_LIMIT)
	if block == 2:
		blockLimits = (TEXT_BLOCK2_START, TEXT_BLOCK2_LIMIT)
	if block == 3:
		blockLimits = (TEXT_BLOCK3_START, TEXT_BLOCK3_LIMIT)
	if block == 4:
		blockLimits = (TEXT_BLOCK4_START, TEXT_BLOCK4_LIMIT)
	if block == 5:
		blockLimits = (TEXT_BLOCK5_START, TEXT_BLOCK5_LIMIT)
	if block == 6:
		blockLimits = (TEXT_BLOCK6_START, TEXT_BLOCK6_LIMIT)
	return blockLimits

if execute_crc32check:
	""" CHECKSUM (CRC32) """
	if crc32(filename) != CRC32:
		sys.exit('ROM CHECKSUM: FAIL')
	else:
		print('ROM CHECKSUM: OK')

if execute_dump:
	""" DUMP """
	conn = sqlite3.connect(db)
	conn.text_factory = str
	cur = conn.cursor()
	id = 1
	with open(filename, 'rb') as f:
		# TEXT POINTERS 1
		pointers = OrderedDict()
		f.seek(POINTER_BLOCK1_START)
		while(f.tell() < POINTER_BLOCK1_END):
			paddress = f.tell()
			pvalue = f.read(2)
			bvalue = f.read(1)
			bvalue2 = (byte2int(bvalue) - 0x80) * 0x8000
			pvalue2 = struct.unpack('H', pvalue)[0] - 0x8000
			pvalue3 = bvalue2 + pvalue2
			if pvalue3 not in pointers:
				pointers[pvalue3] = []
			pointers[pvalue3].append(paddress)
		# TEXT 1
		for pointer in pointers:
			pointer_addresses = ''
			for pointer_address in pointers[pointer]:
				pointer_addresses += str(int2hex(pointer_address)) + ';'
			f.seek(pointer)
			text = b''
			byte = b'1'
			while not byte2int(byte) == table.getNewline():
				if byte2int(byte) == 0xd0 or byte2int(byte) == 0xd1 or byte2int(byte) == 0xd2 or byte2int(byte) == 0xd3  or byte2int(byte) == 0xd4:
					byte = f.read(1)
					text += byte
				byte = f.read(1)
				text += byte
			if len(text) >= 10:
				pre_text = table.separateByteencode(text[:10])
				text_encoded = table.encode(text[10:])
			else:
				pre_text = ''
				text_encoded = table.encode(text)
			# DUMP - DB
			text_binary = sqlite3.Binary(text)
			text_address = int2hex(pointer)
			text_length = len(text_binary)
			block = ys4BlockResolver(pointer)
			cur.execute('insert or replace into texts values (?, ?, ?, ?, ?, ?, ?, ?)', (id, buffer(text_binary), text_encoded, text_address, pointer_addresses, text_length, block, pre_text))
			# DUMP - TXT
			with open('%s - %d.txt' % (dump_path + str(id).zfill(4), len(pointers[pointer])), 'w') as out:
				out.write(text_encoded)
				pass
			id += 1
		# ITEM POINTERS
		pointers = OrderedDict()
		f.seek(POINTER_ITEM_BLOCK_START)
		while(f.tell() < POINTER_ITEM_BLOCK_END):
			paddress = f.tell()
			pvalue = f.read(2)
			pvalue2 = struct.unpack('H', pvalue)[0] + (0x8000 * 8)
			if pvalue2 not in pointers:
				pointers[pvalue2] = []
			pointers[pvalue2].append(paddress)
		# ITEM
		for pointer in pointers:
			pointer_addresses = ''
			for pointer_address in pointers[pointer]:
				pointer_addresses += str(int2hex(pointer_address)) + ';'
			f.seek(pointer)
			text = b''
			byte = b'1'
			while not byte2int(byte) == 0xff:
				byte = f.read(1)
				text += byte
			text_encoded = table.encode(text, dict_resolver=False)
			# DUMP - DB
			text_binary = sqlite3.Binary(text)
			text_address = int2hex(pointer)
			text_length = len(text_binary)
			cur.execute('insert or replace into texts values (?, ?, ?, ?, ?, ?, ?, ?)', (id, buffer(text_binary), text_encoded, text_address, pointer_addresses, text_length, 7, ''))
			# DUMP - TXT
			with open('%s - %d.txt' % (dump_path + str(id).zfill(4), len(pointers[pointer])), 'w') as out:
				out.write(text_encoded)
				pass
			id += 1
		# PLACES POINTERS
		pointers = OrderedDict()
		f.seek(POINTER_PLACES_BLOCK_START)
		while(f.tell() < POINTER_PLACES_BLOCK_END):
			paddress = f.tell()
			pvalue = f.read(2)
			pvalue2 = struct.unpack('H', pvalue)[0] + (0x8000 * 8)
			if pvalue2 not in pointers:
				pointers[pvalue2] = []
			pointers[pvalue2].append(paddress)
		# PLACE
		for pointer in pointers:
			pointer_addresses = ''
			for pointer_address in pointers[pointer]:
				pointer_addresses += str(int2hex(pointer_address)) + ';'
			f.seek(pointer)
			text = b''
			byte = b'1'
			while not byte2int(byte) == 0xff:
				byte = f.read(1)
				text += byte
			text_encoded = table.encode(text)
			# DUMP - DB
			text_binary = sqlite3.Binary(text)
			text_address = int2hex(pointer)
			text_length = len(text_binary)
			cur.execute('insert or replace into texts values (?, ?, ?, ?, ?, ?, ?, ?)', (id, buffer(text_binary), text_encoded, text_address, pointer_addresses, text_length, 8, ''))
			# DUMP - TXT
			with open('%s - %d.txt' % (dump_path + str(id).zfill(4), len(pointers[pointer])), 'w') as out:
				out.write(text_encoded)
				pass
			id += 1
		cur.close()
		conn.commit()
		conn.close()

if execute_inserter:
	conn = sqlite3.connect(db)
	conn.text_factory = str
	cur = conn.cursor()
	with open(filename2, 'r+b') as f:
		# TEXT
		for block in range(1, 7):
			blockLimits = ys4BlockLimitsResolver(block)
			TEXT_BLOCK_START = blockLimits[0]
			TEXT_BLOCK_LIMIT = blockLimits[1]
			# BLOCK X
			f.seek(TEXT_BLOCK_START)
			cur.execute("SELECT text, new_text, text_encoded, id, new_text2, address, pointer_address, size, pre_text, new_pretext FROM texts AS t1 LEFT OUTER JOIN (SELECT * FROM trans WHERE trans.author='%s' AND trans.status = 2) AS t2 ON t1.id=t2.id_text WHERE t1.block = %d" % (user_name, block))
			for row in cur:
				# INSERTER X
				id = row[3]
				original_pretext = row[8]
				original_text = row[2]
				new_text = row[4]
				new_pretext = row[9]
				if (new_text):
					text = new_pretext + new_text
				else:
					text = original_pretext + original_text
				decoded_text = table2.decode(text)
				new_text_address = f.tell()
				f.seek(new_text_address)
				f.write(decoded_text)
				next_text_address = f.tell()
				if next_text_address > (TEXT_BLOCK_LIMIT + 1):
					sys.exit('CRITICAL ERROR! BLOCK %s - TEXT_BLOCK_LIMIT! %s > %s (%s)' % (block, next_text_address, TEXT_BLOCK_LIMIT, (TEXT_BLOCK_LIMIT - next_text_address)))
				# REPOINTER X
				pointer_addresses = row[6]
				if pointer_addresses:
					for pointer_address in pointer_addresses.split(';'):
						if pointer_address:
							pointer_address = hex2dec(pointer_address)
							f.seek(pointer_address)
							bvalue2 = int2byte((new_text_address / 0x8000) + 0x80)
							pvalue2 = int_to_bytes((new_text_address % 0x8000) + 0x8000)
							f.write(pvalue2[1] + pvalue2[0] + bvalue2)
							if pointer_address > (POINTER_BLOCK1_LIMIT + 1):
								sys.exit('CRITICAL ERROR! %d - POINTER_BLOCK_LIMIT! %s > %s (%s)' % (block, pointer_address, POINTER_BLOCK1_LIMIT, (POINTER_BLOCK1_LIMIT - pointer_address)))
				f.seek(next_text_address)
		# PLACES
		f.seek(PLACES_BLOCK_START)
		cur.execute("SELECT text, new_text, text_encoded, id, new_text2, address, pointer_address, size, pre_text, new_pretext FROM texts AS t1 LEFT OUTER JOIN (SELECT * FROM trans WHERE trans.author='%s' AND trans.status = 2) AS t2 ON t1.id=t2.id_text WHERE t1.block = %d" % (user_name, 8))
		for row in cur:
			# INSERTER X
			id = row[3]
			original_pretext = row[8]
			original_text = row[2]
			new_text = row[4]
			new_pretext = row[9]
			if (new_text):
				text = new_pretext + new_text
			else:
				text = original_pretext + original_text
			decoded_text = table2.decode(text)
			new_text_address = f.tell()
			f.seek(new_text_address)
			f.write(decoded_text)
			next_text_address = f.tell()
			if next_text_address > (PLACES_BLOCK_LIMIT + 1):
				sys.exit('CRITICAL ERROR! BLOCK %s - TEXT_BLOCK_LIMIT! %s > %s (%s)' % (8, next_text_address, PLACES_BLOCK_LIMIT, (PLACES_BLOCK_LIMIT - next_text_address)))
			# REPOINTER X
			pointer_addresses = row[6]
			if pointer_addresses:
				for pointer_address in pointer_addresses.split(';'):
					if pointer_address:
						pointer_address = hex2dec(pointer_address)
						f.seek(pointer_address)
						pvalue2 = int_to_bytes(new_text_address - (0x8000 * 8))
						f.write(pvalue2[1] + pvalue2[0])
						if pointer_address > (POINTER_PLACES_BLOCK_LIMIT + 1):
							sys.exit('CRITICAL ERROR! %d - POINTER_BLOCK_LIMIT! %s > %s (%s)' % (8, pointer_address, POINTER_ITEM_BLOCK_LIMIT, (POINTER_PLACES_BLOCK_LIMIT - pointer_address)))
			f.seek(next_text_address)
		last_places_text_address = next_text_address
		# ITEM
		f.seek(ITEM_BLOCK_START)
		cur.execute("SELECT text, new_text, text_encoded, id, new_text2, address, pointer_address, size, pre_text, new_pretext FROM texts AS t1 LEFT OUTER JOIN (SELECT * FROM trans WHERE trans.author='%s' AND trans.status = 2) AS t2 ON t1.id=t2.id_text WHERE t1.block = %d" % (user_name, 7))
		for row in cur:
			# INSERTER X
			id = row[3]
			original_pretext = row[8]
			original_text = row[2]
			new_text = row[4]
			new_pretext = row[9]
			if (new_text):
				text = new_pretext + new_text
			else:
				text = original_pretext + original_text
			decoded_text = table2.decode(text, dict_resolver=False)
			new_text_address = f.tell()
			if (next_text_address + len(decoded_text)) > (ITEM_BLOCK_LIMIT + 1) and next_text_address < PLACES_BLOCK_START:
				new_text_address = last_places_text_address
			f.seek(new_text_address)
			f.write(decoded_text)
			next_text_address = f.tell()
			if next_text_address > (PLACES_BLOCK_LIMIT + 1):
				sys.exit('CRITICAL ERROR! BLOCK %s - PLACES_BLOCK_LIMIT! %s > %s (%s)' % (7, next_text_address, PLACES_BLOCK_LIMIT, (PLACES_BLOCK_LIMIT - next_text_address)))
			# REPOINTER X
			pointer_addresses = row[6]
			if pointer_addresses:
				for pointer_address in pointer_addresses.split(';'):
					if pointer_address:
						pointer_address = hex2dec(pointer_address)
						f.seek(pointer_address)
						pvalue2 = int_to_bytes(new_text_address - (0x8000 * 8))
						f.write(pvalue2[1] + pvalue2[0])
						if pointer_address > (POINTER_ITEM_BLOCK_LIMIT + 1):
							sys.exit('CRITICAL ERROR! %d - POINTER_BLOCK_LIMIT! %s > %s (%s)' % (7, pointer_address, POINTER_ITEM_BLOCK_LIMIT, (POINTER_ITEM_BLOCK_LIMIT - pointer_address)))
			f.seek(next_text_address)
	cur.close()
	conn.close()

if execute_mtefinder:
	""" MTE FINDER """
	with open(filename, 'rb') as f:
		# MTE POINTERS 1
		mte_pointers = []
		f.seek(DICT1_POINTER_BLOCK_START)
		while(f.tell() < DICT1_POINTER_BLOCK_END):
			p_offset = f.tell()
			p_bytes = f.read(2)
			p_value = struct.unpack('H', p_bytes)[0] + (SNES_BANK_SIZE * 0xf)
			pointer = {'offset':p_offset, 'bytes':p_bytes, 'value':p_value}
			mte_pointers.append(pointer)
		for i, p in enumerate(mte_pointers):
			size = len(mte_pointers) - 1
			if i < size:
				f.seek(mte_pointers[i]['value'])
				mte = ''
				byte = b'1'
				while not byte2int(byte) == 0xdf:
					byte = f.read(1)
					if byte2int(byte) != 0xdf:
						mte += byte
				b = (int2hex(i) + '').replace('x', '')
				print '%s=%s' % (b, table.encode(mte))
			else:
				pass

if execute_mteoptimizer:
	""" """
	# DICTIONARY OPTIMIZATION
	with open('mteOptYs4Text-input.txt', 'w') as out:
		conn = sqlite3.connect(db)
		conn.text_factory = str
		cur = conn.cursor()
		cur.execute("SELECT text_encoded, new_text2, address, pointer_address, size FROM texts AS t1 LEFT OUTER JOIN (SELECT * FROM trans WHERE trans.author='%s' AND trans.status = 2) AS t2 ON t1.id=t2.id_text" % user_name)
		for row in cur:
			new_text = row[1]
			original_text = row[0]
			if (new_text):
				text = new_text
			else:
				text = original_text
			text = text.replace('{fe}', '\n')
			text = clean_text(text)
			out.write(text + '\n')
	os.system("mteOpt.py -s \"mteOptYs4Text-input.txt\" -d \"mteOptYs4Text-output.txt\" -m 3 -M 8 -l 1080 -o 53248")
	# OPTIMIZED TABLE
	with open(tablename3, 'rU') as f:
		table3content = f.read()
		with open('mteOptYs4Text-output.txt', 'rU') as f2:
			mteOpt = f2.read()
			with open(tablename2, 'w') as f3:
				f3.write('\n' + table3content)
				f3.write('\n' + mteOpt)
	##
	values = []
	length = 0
	with open('mteOptYs4Text-output.txt', 'rb') as f:
		for line in f:
			parts = line.partition('=')
			value1 = parts[0]
			value2 = parts[2]
			if value2:
				value2 = value2.replace('\n', '').replace('\r', '')
				values.append(value2)
				length += len(value2)
	# INSERTER
	with open(filename2, 'r+b') as f:
		f.seek(DICT1_BLOCK_START)
		for i, value in enumerate(values):
			t_value = table.decode(value, dict_resolver=False) + chr(0xdf)
			if f.tell() + len(t_value) > (DICT1_BLOCK_LIMIT + 1):
				sys.exit('CRITICAL ERROR! MTE INSERTED: %d - TOTAL: %d!' % (i, len(values)))
			f.write(t_value)
	# REPOINTER
	with open(filename2, 'r+b') as f:
		f.seek(DICT1_POINTER_BLOCK_START)
		length = 0
		for i, value in enumerate(values):
			p_value = struct.pack('H', DICT1_BLOCK_START + length - (SNES_BANK_SIZE * 0xf))
			f.write(p_value)
			if f.tell() > (DICT1_POINTER_BLOCK_LIMIT + 1):
				sys.exit('CRITICAL ERROR! MTE REPOINTER!')
			length += len(value) + 1
