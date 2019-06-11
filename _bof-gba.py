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
parser.add_argument('--dump', action='store_true', default=False, help='Execute DUMP')
parser.add_argument('-s', '--source', action='store', dest='source_file', required=True, help='Original filename')
parser.add_argument('-t1', '--table1', action='store', dest='table1', required=True, help='Original table filename')
#parser.add_argument('-db', '--database',  action='store', dest='database_file', required=True, help='DB filename')
#parser.add_argument('-u', '--user', action='store', dest='user', required=True, help='')
args = parser.parse_args()

execute_dump = args.dump
filename = args.source_file
tablename = args.table1
#db = args.database_file
#user_name = args.user
dump_path = 'bof/gba/dump/'

TEXT_BLOCK1_START = 0x318fb0
TEXT_BLOCK1_END = TEXT_BLOCK1_LIMIT = 0x3307ff

table = Table(tablename)

if execute_dump:
	""" DUMP """
	"""
	conn = sqlite3.connect(db)
	conn.text_factory = str
	cur = conn.cursor()
	"""
	id = 1
	with open(filename, 'rb') as f:
		f.seek(TEXT_BLOCK1_START)
		while(f.tell() < TEXT_BLOCK1_LIMIT):
			text = b''
			byte = b'1'
			while not byte2int(byte) == table.getNewline():
				if byte2int(byte) in (0x03, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c):
					byte = f.read(1)
					text += byte
				byte = f.read(1)
				text += byte
			text_encoded = table.encode(text, cmd_list=[0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c])
			print text_encoded
			# DUMP - DB
			text_binary = sqlite3.Binary(text)
			#text_address = int2hex(pointer)
			text_length = len(text_binary)
			block = 1
			#cur.execute('insert or replace into texts values (?, ?, ?, ?, ?, ?, ?)', (id, buffer(text_binary), text_encoded, text_address, pointer_addresses, text_length, block))
			# DUMP - TXT
			with open('%s.txt' % (dump_path + str(id).zfill(4)), 'w') as out:
				out.write(text_encoded)
				pass
			id += 1
		"""
		cur.close()
		conn.commit()
		conn.close()
		"""