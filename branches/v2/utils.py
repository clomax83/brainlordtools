__author__ = "Roberto Fontanarosa"
__license__ = "GPL"
__version__ = ""
__maintainer__ = "Roberto Fontanarosa"
__email__ = "robertofontanarosa@gmail.com"

def int2byte(n):
	""" convert an integer to a byte """
	return chr(n)

def byte2int(b):
	""" returns an integer representing a 8-bit string """
	return ord(b)

def byte22int(b2):
	return (ord(b2[0]) << 8) + ord(b2[1])

def byte32int(b3):
	return (ord(b3[2]) << 16) + (ord(b3[1]) << 8) + ord(b3[0])

def int2hex(n):
	""" convert an integer number to a hexadecimal string """
	return hex(n)

def hex2dec(s):
	""" convert a hexadecimal string to an integer """
	return int(s, 16)

def string_address2int_address(s, switch=False, offset=0):
	"""  """
	if (switch):
		n = byte2int(s[0]) + (byte2int(s[1]) << 8) + offset
	else:
		n = (byte2int(s[0]) << 8) + byte2int(s[1]) + offset
	return n

def int_address2string_address(n, switch=False, shift=0):
	import binascii
	h = int2hex(n)
	s = binascii.unhexlify(h[shift:])
	if (switch):
		s = s[1] + s[0]
	return s

#######
# ROM #
#######

def crc32(file):
	import zlib
	prev = 0
	for eachLine in open(file, 'rb'):
		prev = zlib.crc32(eachLine, prev)
	return '%X' % (prev & 0xFFFFFFFF)

def hasHeader(file):
	import os
	size = os.path.getsize(file)
	return size == 512

########
# TEST #
########

def test():
	s = "a"
	i = 97
	h = "61"
	print byte2int(s) == i
	print int2byte(i) == s
	print hex2dec(h) == i