import sys

from .lib import (
    validate_commands_config,
    validate_options_config,
    humblecall,
    get_arg_type,
    get_equivalent_commands,
    get_options_equivalency,
    expand_commands_config_keys,
)


class QuickParse(object):

    ERROR_TYPE_VALIDATION = 0
    ERROR_VALUE_NOT_FOUND = 1
    ERROR_INCOMPLETE_COMMAND = 2

    def __init__(self, commands_config = None, options_config = None, cli_args = None):
        if cli_args is None:
            self.args = tuple(sys.argv[1:])
        else:
            if not (isinstance(cli_args, (list, tuple)) and all(isinstance(element, str) for element in cli_args)):
                raise ValueError(f"cli_args must be a list of strings")
            self.args = tuple(cli_args[:])
        self.commands_config = commands_config
        self.options_config = options_config
        try:
            validate_commands_config(self.commands_config)
            validate_options_config(self.options_config)
        except AssertionError as ae:
            raise ValueError(ae) from ae
        self._expanded_commands_config = expand_commands_config_keys(self.commands_config)
        self._options_equivalency = get_options_equivalency(self.options_config)
        self.commands = list()
        self.parameters = list()
        self.options = dict()
        self.non_commands = list()
        self.errors = dict()
        self.to_execute = None
        self.numeric = None
        self.plusnumeric = None
        self._process_args()

    def execute(self, *_args, **kwargs):
        kwargs.setdefault('quickparse', self)
        return_values = list()
        if isinstance(self.to_execute, tuple):
            for try_to_call in self.to_execute:
                return_values.append(humblecall(try_to_call, *_args, **kwargs))
            return_values = tuple(return_values)
        else:
            return_values = humblecall(self.to_execute, *_args, **kwargs)
        return return_values

    def _process_args(self):
        command_level = self._expanded_commands_config
        parameters_only_turned_on = False
        arg_index = 0
        while arg_index < len(self.args):
            arg = self.args[arg_index]
            arg_index += 1

            if arg == '':
                continue

            self.non_commands.append(arg)
            arg_type = get_arg_type(arg)

            if not parameters_only_turned_on and arg_type == 'parameters only separator':
                parameters_only_turned_on = True

            elif parameters_only_turned_on:
                try:
                    self.parameters.append(int(arg))
                except ValueError:
                    try:
                        self.parameters.append(float(arg))
                    except ValueError:
                        self.parameters.append(arg)

            elif arg_type == 'numeric':
                if arg[0] == '-':
                    self.numeric = int(arg[1:])
                else: # '+'
                    self.plusnumeric = int(arg[1:])

            elif arg_type in ('single letter', 'doubleminus option') or \
                (arg_type == 'long option' and arg in self._options_equivalency):
                validator = self._get_default_validator(arg)
                if validator in (None, bool):
                    self._add_option_equivalents(arg, True)
                else:
                    if arg_index >= len(self.args):
                        self._add_error(self.ERROR_VALUE_NOT_FOUND, arg, f"No value got for '{arg}' - validator: {validator.__name__}")
                        self._validate_and_add(arg, True, lambda x: x)
                        continue
                    next_arg = self.args[arg_index]
                    arg_index += 1
                    self._validate_and_add(arg, next_arg, validator)

            elif arg_type == 'option and value':
                key, value = arg.split('=', 1)
                validator = self._get_default_validator(key)
                if validator in (None, bool):
                    if validator == bool:
                        self._add_error(self.ERROR_TYPE_VALIDATION, key, f"Bool option '{key}' got a value '{value}'")
                    self._add_option_equivalents(key, value)
                else:
                    self._validate_and_add(key, value, validator)

            elif arg_type == 'long option' or (arg_type == 'potential letter and value' and self._get_default_validator(arg[0:2]) not in (None, bool)):
                first_letter_validator = self._get_default_validator(arg[0:2])
                if first_letter_validator not in (None, bool):
                    self._validate_and_add(arg[0:2], arg[2:], first_letter_validator)
                    continue
                unpackable = '-' not in arg[1:]
                if unpackable:
                    unpacked = list()
                    prefix = arg[0]
                    for letter in arg[1:]:
                        unpacked.append(f"{prefix}{letter}")
                    if all(self._get_default_validator(option) in (None, bool) for option in unpacked):
                        for option in unpacked:
                            self._add_option_equivalents(option, True)
                        continue
                self._add_option_equivalents(arg, True)

            else:
                # arg_type == 'param or command'
                # or
                # arg_type == 'potential letter and value' and self._get_default_validator(arg[0:2]) in (None, bool)
                if isinstance(command_level, dict) and arg in command_level:
                    self.commands.append(arg)
                    self.non_commands.pop()
                    command_level = command_level[arg]
                else:
                    try:
                        self.parameters.append(int(arg))
                    except ValueError:
                        try:
                            self.parameters.append(float(arg))
                        except ValueError:
                            self.parameters.append(arg)

        self.commands = get_equivalent_commands(self.commands, self.commands_config)
        self.parameters = tuple(self.parameters)
        self.non_commands = tuple(self.non_commands)

        if isinstance(command_level, dict):
            if '' in command_level:
                if isinstance(command_level[''], (list, tuple)):
                    self.to_execute = tuple(command_level[''])
                else:
                    self.to_execute = command_level['']
            else:
                self._add_error(self.ERROR_INCOMPLETE_COMMAND, self.commands, f"Incomplete command: '{' '.join(self.commands)}'")
        else:
            if isinstance(command_level, (list, tuple)):
                self.to_execute = tuple(command_level)
            else:
                self.to_execute = command_level

    def _validate_and_add(self, option, value, validator):
        try:
            valid = validator(value)
        except Exception as e:
            self._add_option_equivalents(option, value)
            self._add_error(self.ERROR_TYPE_VALIDATION, option, f"Validation error while validating '{value}' for '{option}': {e}")
        else:
            self._add_option_equivalents(option, valid)

    def _add_option_equivalents(self, option, value):
        self.options[option] = value
        for eq_option in self._options_equivalency.get(option, {}).get('equivalents', ()):
            self.options[eq_option] = value

    def _get_default_validator(self, option):
        return self._options_equivalency.get(option, {}).get('validator', None)

    def _add_error(self, type, target, message):
        equivalent_targets = self._options_equivalency.get(target, {}).get('equivalents', (target, ))
        self.errors[equivalent_targets] = {'type': type, 'message': message}
