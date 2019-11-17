import sys
import re

numericflag_re = re.compile('^-\\d+$')


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

	def reparse(self, *args, **kwargs):

		def set_up_config(*args, **kwargs):
			self.config = dict()
			self.config['subcommands'] = args

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
