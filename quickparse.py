import sys
import re
from copy import deepcopy

from pprint import pprint as pp
from pprint import pformat as pf
from pdb import set_trace as trace

numericflag_re = re.compile('^-\\d+$')


# lib

def get_all_strings_from_nested_structure(nested, theset):
	if isinstance(nested, str):
		if len(nested) > 0:
			theset = theset.union({nested,})
	elif isinstance(nested, int):
		theset = theset.union({str(nested),})
	elif isinstance(nested, (list, tuple, set)):
		if len(nested) > 0:
			for item in nested:
				theset = get_all_strings_from_nested_structure(item, theset)
	else:
		raise TypeError('nested structure contains items other than strings')
	return theset


# classes

class QuickParse(object):

	config = None
	command = None
	numericflag = None
	flags = None
	subcommands = None
	parameters = None
	is_empty = None

	def __init__(self, *args, **kwargs):
		self.reparse(*args, **kwargs)

	def __str__(self):
		components = dict()
		components['config'] = self.config
		components['command'] = self.command
		components['numericflag'] = self.numericflag
		components['flags'] = self.flags
		components['subcommands'] = self.subcommands
		components['parameters'] = self.parameters
		return pf(components)

	def reparse(self, *args, **kwargs):

		def set_up_config(*args, **kwargs):
			if len(args) == 1 and isinstance(args[0], dict):
				self.config = deepcopy(args[0])
			else:
				self.config = dict()
				self.config['subcommands'] = get_all_strings_from_nested_structure(args, set())

		def set_single_numericflag_if_dash_plus_digits(argument):
			if numericflag_re.search(argument):
				if self.numericflag:
					raise Exception('only one numeric flag is allowed')
				self.numericflag = int(argument[1:])
				return True
			return False

		def add_to_flags_if_dash_plus_single_char(argument):
			if len(argument) == 2 and argument[0] == '-':
				self.flags = self.flags.union({argument[1]})
				return True
			return False

		def add_to_flags_if_double_dash_plus_string(argument):
			if len(argument) > 2 and argument[0:2] == '--':
				self.flags = self.flags.union({argument[2:]})
				return True
			return False

		def add_to_subcommands_if_on_the_list(argument):
			if argument in self.config['subcommands']:
				self.subcommands += (argument, )
				return True
			return False

		def add_to_parameters(argument):
			self.parameters += (argument, )
			return True

		set_up_config(*args, **kwargs)

		self.command = sys.argv[0]
		self.numericflag = None
		self.flags = set()
		self.subcommands = tuple()
		self.parameters = tuple()
		self.is_empty = len(sys.argv) <= 1

		for argument in sys.argv[1:]:
			for fn in (
				set_single_numericflag_if_dash_plus_digits,
				add_to_flags_if_dash_plus_single_char,
				add_to_flags_if_double_dash_plus_string,
				add_to_subcommands_if_on_the_list,
				add_to_parameters,
			):
				if fn(argument):
					break

		return self
