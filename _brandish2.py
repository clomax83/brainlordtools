__author__ = "Roberto Fontanarosa"
__license__ = "GPLv2"
__version__ = ""
__maintainer__ = "Roberto Fontanarosa"
__email__ = "robertofontanarosa@gmail.com"

import sys, os, struct, sqlite3
from collections import OrderedDict

from _rhtools.utils import *
from _rhtools.Table import Table

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--crc32check', action='store_true', default=False, help='Execute CRC32CHECK')
parser.add_argument('--dump', action='store_true', default=False, help='Execute DUMP')
parser.add_argument('--insert', action='store_true', default=False, help='Execute INSERTER')
parser.add_argument('-s', '--source', action='store', dest='source_file', required=True, help='Original filename')
parser.add_argument('-d', '--dest',  action='store', dest='dest_file', required=True, help='Destination filename')
parser.add_argument('-t1', '--table1', action='store', dest='table1', required=True, help='Original table filename')
parser.add_argument('-t2', '--table2', action='store', dest='table2', required=True, help='Modified table filename')
parser.add_argument('-db', '--database',  action='store', dest='database_file', required=True, help='DB filename')
parser.add_argument('-u', '--user', action='store', dest='user', required=True, help='')
args = parser.parse_args()

execute_crc32check = args.crc32check
execute_dump = args.dump
execute_inserter = args.insert
filename = args.source_file
filename2 = args.dest_file
tablename = args.table1
tablename2 = args.table2
db = args.database_file
user_name = args.user
dump_path = './resources/brandish2/dump/'

SNES_HEADER_SIZE = 0x200
SNES_BANK_SIZE = 0x8000

CRC32 = '9DB396EC'

TEXT_BLOCK_START = 0x280787
TEXT_BLOCK_END = TEXT_BLOCK_LIMIT = 0x28e189
TEXT_BLOCK_SIZE = TEXT_BLOCK_END - TEXT_BLOCK_START
TEXT_BLOCK_MAX_SIZE = TEXT_BLOCK_LIMIT - TEXT_BLOCK_START

TEXT_POINTER_BLOCK_START = 0x280029
TEXT_POINTER_BLOCK_END = TEXT_POINTER_BLOCK_LIMIT = 0x280786

table = Table(tablename)
table2 = Table(tablename2)

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
	with open(filename, "rb") as f:
		# POINTERS
		pointers = {}
		f.seek(TEXT_POINTER_BLOCK_START)
		while(f.tell() < TEXT_POINTER_BLOCK_END):
			pointer_address = f.tell()
			pointer_value = string_address2int_address(f.read(2), switch=True, offset=2621440)
			if pointer_value not in pointers:
				pointers[pointer_value] = [pointer_address]
			else:
				pointers[pointer_value].append(pointer_address)
		# TEXT
		pointers_found = []
		id = 1
		f.seek(TEXT_BLOCK_START)
		while(f.tell() < TEXT_BLOCK_END):
			text = b''
			byte = b'1'
			curr_pointer_value = f.tell()
			pointer_addresses = ''
			if id in (44, 782, 783, 792, 793, 798, 799, 806, 807, 815, 816, 820, 821, 830, 831, 839, 840, 848, 849, 853, 854, 862, 863, 871, 872, 877, 878):
				curr_pointer_value = curr_pointer_value + 3
			if id == 498:
				curr_pointer_value = curr_pointer_value + 1
			if curr_pointer_value in pointers:
				for pointer_address in pointers[curr_pointer_value]:
					pointer_addresses += str(int2hex(pointer_address)) + ';'
					pointers_found.append(curr_pointer_value)
			else:
				print('Pointer Not found: ' + str(id) + ' - ' + hex(curr_pointer_value))
			while not byte2int(byte) == table.getNewline():
				byte = f.read(1)
				text += byte
			text_encoded = table.encode(text, separated_byte_format=True)
			# DUMP - DB
			text_binary = sqlite3.Binary(text)
			text_address = int2hex(curr_pointer_value)
			text_length = len(text_binary)
			cur.execute('insert or replace into texts values (?, ?, ?, ?, ?, ?)', (id, buffer(text_binary), text_encoded, text_address, pointer_addresses, text_length))
			# DUMP - TXT
			with open('%s - %s.txt' % (dump_path + str(id).zfill(3), pointer_addresses), 'w') as out:
				out.write(text_encoded)
				pass
			id += 1
		for key in pointers:
			if key not in pointers_found:
				print('Pointer Not used: ' + hex(key) + ' Values: ' + str(pointers[key]))
	cur.close()
	conn.commit()
	conn.close()

if execute_inserter:
	""" REPOINTER """
	conn = sqlite3.connect(db)
	conn.text_factory = str
	cur = conn.cursor()
	import codecs
	with open(filename2, 'r+b') as f:
		f.seek(TEXT_BLOCK_START)
		cur.execute("SELECT text, new_text, text_encoded, id, new_text2, address, pointer_address FROM texts AS t1 LEFT OUTER JOIN (SELECT * FROM trans WHERE trans.author='%s' AND trans.status = 2) AS t2 ON t1.id=t2.id_text" % user_name)
		for row in cur:
			# INSERTER
			id = row[3]
			original_text = row[2]
			new_text = row[4]
			if (new_text):
				text = new_text
				decoded_text = table2.decode(text, True)
			else:
				text = original_text
				decoded_text = table.decode(text, True)
			new_text_address = f.tell()
			f.seek(new_text_address)
			f.write(decoded_text)
			next_text_address = f.tell()
			if next_text_address > (TEXT_BLOCK_LIMIT + 1):
				sys.exit('CRITICAL ERROR! TEXT_BLOCK_LIMIT! %s > %s (%s)' % (next_text_address, TEXT_BLOCK_LIMIT, (TEXT_BLOCK_LIMIT - next_text_address)))
			# REPOINTER
			pointer_addresses = row[6]
			if pointer_addresses:
				for pointer_address in pointer_addresses.split(';'):
					if pointer_address:
						pointer_address = hex2dec(pointer_address)
						f.seek(pointer_address)
						if id in (44, 782, 783, 792, 793, 798, 799, 806, 807, 815, 816, 820, 821, 830, 831, 839, 840, 848, 849, 853, 854, 862, 863, 871, 872, 877, 878):
							new_text_address = new_text_address + 3
						if id == 498:
							new_text_address = new_text_address + 1
						f.write(int_address2string_address2(new_text_address-2621440, switch=True, shift=2))
						if pointer_address > (TEXT_POINTER_BLOCK_LIMIT + 1):
							sys.exit('CRITICAL ERROR! TEXT_POINTER_BLOCK_LIMIT! %s > %s (%s)' % (pointer_address, TEXT_POINTER_BLOCK_LIMIT, (TEXT_POINTER_BLOCK_LIMIT - pointer_address)))
			f.seek(next_text_address)
	cur.close()
	conn.close()
