# -*- coding: utf-8 -*-

import sys, os, re, io
from shutil import copyfile
from collections import defaultdict, Counter, OrderedDict

import argparse
parent_parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(add_help=False) 
subparsers = parser.add_subparsers(dest='cmd')
parent_parser.add_argument('-m', '--min', action='store', dest='min', type=int, default=3, help='')
parent_parser.add_argument('-M', '--max',  action='store', dest='max', type=int, default=8, help='')
parent_parser.add_argument('-l', '--limit',  action='store', dest='limit', type=int, default=5, help='')
parent_parser.add_argument('-s', '--source', action='store', dest='source_file', required=True, help='Original filename')
parent_parser.add_argument('-c', '--clean', action='store', dest='clean_file', required=True, help='Clean filename')
parent_parser.add_argument('-g', '--game', choices=['smrpg', 'bof', 'ys4'], help='Game specific cleaning rules')
parser0 = subparsers.add_parser('print' , parents=[parent_parser], add_help=False)
parser1 = subparsers.add_parser('table', parents=[parent_parser], add_help=False)
parser1.add_argument('-d', '--dest', action='store', dest='dest_file', required=True, help='Destination filename')
parser1.add_argument('-o', '--offset', action='store', dest='offset', type=int, help='Starting offset')
args = parser.parse_args()
dict_args = vars(args)

cmd = dict_args.get('cmd')
MIN = dict_args.get('min')
MAX = dict_args.get('max')
LIMIT = dict_args.get('limit')
filename = dict_args.get('source_file')
filename1 = dict_args.get('clean_file')
game = dict_args.get('game')
filename2 = dict_args.get('dest_file')
offset = dict_args.get('offset')

def clean_file(filename, filename1, regex_list=None, allow_duplicates=True):
	""" applica a ogni linea del file delle espressioni regolari, rimuove opzionalmente le linee duplicate """
	with io.open(filename, mode='r', encoding="utf-8") as f, io.open(filename1, mode='w', encoding="utf-8") as f1:
		lines_seen = set()
		for line in f.readlines():
			if regex_list:
				for regex in regex_list:
					line = regex[0].sub(regex[1], line)
			if allow_duplicates:
				f1.write(line)
			elif line not in lines_seen:
				f1.write(line)
				lines_seen.add(line)

def extract_chunks(text, chunk_size, start_index=0):
	""" estrae le occorrenze di lunghezza n da una stringa """
	return [text[i:(i+chunk_size)] for i in range(start_index, len(text), chunk_size)]

def get_substrings_by_length(text, length):
	""" estrae tutte le possibili occorrenze di lunghezza n da una stringa """
	chunks = []
	if length > 0:
		for i in range (0, length):
			chunks += extract_chunks(text, length, i)
	return list(filter(lambda x: len(x) == length, chunks))

def get_occurrences_by_length(filename, length):
	""" genera un dizionario con le occorrenze di lunghezza n """
	dictionary = defaultdict(int)
	with io.open(filename, mode='r', encoding="utf-8") as f:
		for line in f.readlines():
			if line:
				line = line.rstrip('\r\n')
				substrings = get_substrings_by_length(line, length)
				for string in substrings: dictionary[string] += 1
	return dictionary

def get_occurrences(filename, min_length, max_length):
	""" genera un dizionario con le occorrenze di un range di lunghezza """
	dictionary = Counter()
	for length in range(min_length, max_length + 1):
		occurrences = Counter(get_occurrences_by_length(filename, length))
		dictionary.update(occurrences)
	return dictionary

def calculate_weight(dictionary):
	""" crea un dizionario pesato sulla lunghezza delle parole """
	return {k: v * (len(k) - 2) for k, v in dictionary.items()}

def sort_dict_by_value(dictionary, reverse=True):
	""" reversa il dizionario e lo ordina per valore """
	return sorted(dictionary.iteritems(), key=lambda(k,v):(v,k), reverse=reverse)

def export_table(filename, dictionary, offset):
	with io.open(filename, mode='w', encoding="utf-8") as out:
		for i, v in enumerate(dictionary):
			line = v
			if offset is not None:
				n = hex(i + offset).rstrip('L')
				b = (n + '').replace('0x', '')
				b = b.zfill(4)
				line = "%s=%s" % (b, v)
			out.write(line + '\n')

regex_list = None
if game == 'bof':
	pass
elif game == 'smrpg':
	regex_list = [
		(re.compile(r'^.{7}'), ''),
		(re.compile(r' {5,}'), ''),
		(re.compile(r'[.]{3,}'), '\n'),
		(re.compile(r'\[.+?\]'), '\n')
	]
elif game == 'ys4':
	pass

clean_file(filename, filename1, regex_list=regex_list, allow_duplicates=False)
dictionary = OrderedDict()
curr_filename = filename1
for i in range(0, LIMIT):
	next_filename = filename1 + '.' + str(i)
	occurrences = get_occurrences(curr_filename, MIN, MAX)
	occurrences_with_weight = calculate_weight(occurrences)
	sorted_dicionary = sort_dict_by_value(occurrences_with_weight)
	k, v = sorted_dicionary[0]
	dictionary[k] = v
	clean_file(curr_filename, next_filename, regex_list=[(re.compile(re.escape(k)), '\n')], allow_duplicates=True)
	curr_filename = next_filename

if cmd == 'print':
	print(dictionary)
elif cmd == 'table':
	print(dictionary)
	export_table(filename2, dictionary, offset)
