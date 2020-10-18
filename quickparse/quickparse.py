import sys
from collections.abc import Iterable, Sequence

from .lib import (
    validate_commands_config,
    validate_options_config,
    humblecall,
    get_arg_type,
    get_equivalent_commands,
    get_options_equivalency,
    expand_commands_config_keys,
    is_non_stringlike_sequence,
)


class QuickParse(object):

    ERROR_TYPE_VALIDATION = 0
    ERROR_VALUE_NOT_FOUND = 1
    ERROR_INCOMPLETE_COMMAND = 2

    def __init__(self, commands_config = None, options_config = None, cli_args = None):
        if cli_args is None:
            self.args = tuple(sys.argv[1:])
        else:
            if not (isinstance(cli_args, Iterable) and all(isinstance(element, str) for element in cli_args)):
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

    @property
    def has_errors(self):
        return len(self.errors) > 0

    @property
    def error_messages(self):
        return set(error['message'] for error in self.errors.values())

    def validate(self, validator):
        if not isinstance(validator, dict):
            raise RuntimeError(f"Validator must be a dict")
        parameters_validator = validator.get('parameters', dict())
        if len(parameters_validator) > 0:
            self._validate_parameters(parameters_validator)
        options_validator = validator.get('options', dict())
        if len(options_validator) > 0:
            self._validate_options(options_validator)
        numeric_validator = validator.get('numeric', dict())
        if len(numeric_validator) > 0:
            self._validate_numeric(numeric_validator)
        plusnumeric_validator = validator.get('plusnumeric', dict())
        if len(plusnumeric_validator) > 0:
            self._validate_numeric(plusnumeric_validator, numeric_type='plusnumeric')

    def _validate_parameters(self, parameters_validator):
        count = parameters_validator.get('count')
        mincount = parameters_validator.get('mincount')
        maxcount = parameters_validator.get('maxcount')
        if count is not None:
            try:
                count = int(count)
            except TypeError:
                raise RuntimeError(f"Validator>parameter>count must be an integer")
            if mincount is not None or maxcount is not None:
                raise RuntimeError(f"Validator>parameter>count is mutually exclusive with mincount and maxcount")
            if len(self.parameters) != count:
                if count == 0:
                    self._add_error(self.ERROR_TYPE_VALIDATION, 'parameters.count', f"No parameters expected")
                else:
                    self._add_error(self.ERROR_TYPE_VALIDATION, 'parameters.count', f"{count} parameters expected, got {len(self.parameters)}")
        else:
            if mincount is not None:
                try:
                    mincount = int(mincount)
                except TypeError:
                    raise RuntimeError(f"Validator>parameter>mincount must be an integer")
                if len(self.parameters) < mincount:
                    self._add_error(self.ERROR_TYPE_VALIDATION, 'parameters.mincount', f"Minimum number of parameters: {mincount}")
            if maxcount is not None:
                try:
                    maxcount = int(maxcount)
                except TypeError:
                    raise RuntimeError(f"Validator>parameter>maxcount must be an integer")
                if len(self.parameters) > maxcount:
                    if maxcount == 0:
                        self._add_error(self.ERROR_TYPE_VALIDATION, 'parameters.maxcount', f"No parameters expected")
                    else:
                        self._add_error(self.ERROR_TYPE_VALIDATION, 'parameters.maxcount', f"Maximum number of parameters: {maxcount}")

    def _validate_options(self, options_validator):
        mandatory = options_validator.get('mandatory')
        if 'optional' in options_validator:
            optional = options_validator['optional']
            if optional is None:
                optional = tuple()
        else:
            optional = None
        forbidden = options_validator.get('forbidden')
        mandatory_with_equivalents_flat = set()
        if mandatory is not None:
            if isinstance(mandatory, str):
                mandatory = (mandatory, )
            if not isinstance(mandatory, Iterable) or not all(isinstance(option, str) for option in mandatory):
                raise RuntimeError(f"Validator>options>mandatory must be a string or list of strings")
            mandatory_with_equivalents = set()
            mandatory_with_equivalents_flat = set()
            for option in mandatory:
                equivalents = self._options_equivalency.get(option, {}).get('equivalents', (option, ))
                mandatory_with_equivalents.add(tuple(sorted(equivalents)))
                mandatory_with_equivalents_flat.update(equivalents)
            missing_mandatory_with_equivalents = set()
            for option in mandatory_with_equivalents:
                if option[0] not in self.options:
                    missing_mandatory_with_equivalents.add(option)
            if len(missing_mandatory_with_equivalents) > 0:
                missing_mandatory_strs = tuple('/'.join(option_equivalents) for option_equivalents in missing_mandatory_with_equivalents)
                self._add_error(self.ERROR_TYPE_VALIDATION, 'options.mandatory', \
                    f"Mandatory options missing: {', '.join(missing_mandatory_str for missing_mandatory_str in missing_mandatory_strs)}")
        if optional is not None:
            if isinstance(optional, str):
                optional = (optional, )
            if not isinstance(optional, Iterable) or not all(isinstance(option, str) for option in optional):
                raise RuntimeError(f"Validator>options>optional must be a string or list of strings")
            mandatory_and_optional_with_equivalents_flat = set(mandatory_with_equivalents_flat)
            for option in optional:
                mandatory_and_optional_with_equivalents_flat.update(self._options_equivalency.get(option, {}).get('equivalents', (option, )))
            forbidden_with_equivalents_flat = set()
            for option in self.options:
                if option not in mandatory_and_optional_with_equivalents_flat:
                    forbidden_with_equivalents_flat.add(option)
            forbidden_with_equivalents = set()
            for option in forbidden_with_equivalents_flat:
                equivalents = self._options_equivalency.get(option, {}).get('equivalents', (option, ))
                forbidden_with_equivalents.add(tuple(sorted(equivalents)))
            if len(forbidden_with_equivalents) > 0:
                forbidden_strs = tuple('/'.join(option_equivalents) for option_equivalents in forbidden_with_equivalents)
                self._add_error(self.ERROR_TYPE_VALIDATION, 'options.optional', \
                    f"Option not applicable: {', '.join(forbidden_str for forbidden_str in forbidden_strs)}")
        if forbidden is not None:
            if isinstance(forbidden, str):
                forbidden = (forbidden, )
            if not isinstance(forbidden, Iterable) or not all(isinstance(option, str) for option in forbidden):
                raise RuntimeError(f"Validator>options>forbidden must be a string or list of strings")
            forbidden_with_equivalents_flat = set()
            for option in self.options:
                if option in forbidden:
                    forbidden_with_equivalents_flat.update(self._options_equivalency.get(option, {}).get('equivalents', (option, )))
            forbidden_with_equivalents = set()
            for option in forbidden_with_equivalents_flat:
                equivalents = self._options_equivalency.get(option, {}).get('equivalents', (option, ))
                forbidden_with_equivalents.add(tuple(sorted(equivalents)))
            if len(forbidden_with_equivalents) > 0:
                forbidden_strs = tuple('/'.join(option_equivalents) for option_equivalents in forbidden_with_equivalents)
                self._add_error(self.ERROR_TYPE_VALIDATION, 'options.forbidden', \
                    f"Option not applicable: {', '.join(forbidden_str for forbidden_str in forbidden_strs)}")

    def _validate_numeric(self, numeric_validator, *, numeric_type = None):
        count = numeric_validator.get('count')
        mincount = numeric_validator.get('mincount')
        maxcount = numeric_validator.get('maxcount')
        if numeric_type == 'plusnumeric':
            numeric_flags = self.plusnumeric if isinstance(self.plusnumeric, Sequence) else (self.plusnumeric, ) if self.plusnumeric is not None else None
            msg_key = 'plusnumeric'
        else:
            numeric_flags = self.numeric if isinstance(self.numeric, Sequence) else (self.numeric, ) if self.numeric is not None else None
            msg_key = 'numeric'
        if count is not None:
            try:
                count = int(count)
            except TypeError:
                raise RuntimeError(f"Validator>{msg_key}>count must be an integer")
            if mincount is not None or maxcount is not None:
                raise RuntimeError(f"Validator>{msg_key}>count is mutually exclusive with mincount and maxcount")
            if numeric_flags is None:
                if count != 0:
                    self._add_error(self.ERROR_TYPE_VALIDATION, f"{msg_key}.count", f"{count} {msg_key} flag{'s' if count > 0 else ''} expected")
            else:
                if len(numeric_flags) != count:
                    if count == 0:
                        self._add_error(self.ERROR_TYPE_VALIDATION, f"{msg_key}.count", f"{msg_key.capitalize()} flags are not applicable")
                    else:
                        self._add_error(self.ERROR_TYPE_VALIDATION, f"{msg_key}.count", f"Expected {count} {msg_key} flags, got {len(numeric_flags)}")
        else:
            if mincount is not None:
                try:
                    mincount = int(mincount)
                except TypeError:
                    raise RuntimeError(f"Validator>{msg_key}>mincount must be an integer")
                if (numeric_flags is None and mincount > 0) or (numeric_flags is not None and len(numeric_flags) < mincount):
                    self._add_error(self.ERROR_TYPE_VALIDATION, f"{msg_key}.mincount", f"Minimum number of {msg_key} flags: {mincount}")
            if maxcount is not None:
                try:
                    maxcount = int(maxcount)
                except TypeError:
                    raise RuntimeError(f"Validator>{msg_key}>maxcount must be an integer")
                if (numeric_flags is None and maxcount < 0) or (numeric_flags is not None and len(numeric_flags) > maxcount):
                    if maxcount == 0:
                        self._add_error(self.ERROR_TYPE_VALIDATION, f"{msg_key}.maxcount", f"{msg_key.capitalize()} flags are not applicable")
                    else:
                        self._add_error(self.ERROR_TYPE_VALIDATION, f"{msg_key}.maxcount", f"Maximum number of {msg_key} flags: {maxcount}")

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
                numeric_val = int(arg[1:])
                if arg[0] == '-':
                    if self.numeric is None:
                        self.numeric = numeric_val
                    else:
                        if not isinstance(self.numeric, tuple):
                            self.numeric = (self.numeric, )
                        self.numeric += (numeric_val, )
                else: # '+'
                    if self.plusnumeric is None:
                        self.plusnumeric = numeric_val
                    else:
                        if not isinstance(self.plusnumeric, tuple):
                            self.plusnumeric = (self.plusnumeric, )
                        self.plusnumeric += (numeric_val, )

            elif arg_type in ('single letter', 'doubleminus option') or \
                (arg_type == 'long option' and arg in self._options_equivalency):
                validator = self._get_default_validator(arg)
                if validator in (None, bool):
                    self._add_option_equivalents(arg, True)
                else:
                    if arg_index >= len(self.args):
                        equivalents_str = '/'.join(self._options_equivalency.get(arg, {}).get('equivalents', ()))
                        self._add_error(self.ERROR_VALUE_NOT_FOUND, arg, f"No value got for '{equivalents_str}' - validator: {validator.__name__}")
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
                    validated_options = tuple(option for option in unpacked if self._get_default_validator(option) not in (None, bool))
                    if len(validated_options) <= 1:
                        for option in unpacked:
                            if option not in validated_options:
                                self._add_option_equivalents(option, True)
                        if len(validated_options) == 1:
                            option = validated_options[0]
                            validator = self._get_default_validator(option)
                            if arg_index >= len(self.args):
                                equivalents_str = '/'.join(self._options_equivalency.get(option, {}).get('equivalents', ()))
                                self._add_error(self.ERROR_VALUE_NOT_FOUND, option, f"No value got for '{equivalents_str}' - validator: {validator.__name__}")
                                self._validate_and_add(option, True, lambda x: x)
                                continue
                            next_arg = self.args[arg_index]
                            arg_index += 1
                            self._validate_and_add(option, next_arg, validator)
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
                if is_non_stringlike_sequence(command_level['']):
                    self.to_execute = tuple(command_level[''])
                else:
                    self.to_execute = command_level['']
            else:
                self._add_error(self.ERROR_INCOMPLETE_COMMAND, self.commands, f"Incomplete command: '{' '.join(self.commands)}'")
        else:
            if is_non_stringlike_sequence(command_level):
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
        if option in self.options:
            if not isinstance(self.options[option], tuple):
                self.options[option] = (self.options[option], )
            self.options[option] += (value, )
        else:
            self.options[option] = value
        for eq_option in self._options_equivalency.get(option, {}).get('equivalents', ()):
            self.options[eq_option] = self.options[option]

    def _get_default_validator(self, option):
        return self._options_equivalency.get(option, {}).get('validator', None)

    def _add_error(self, type, target, message):
        equivalent_targets = self._options_equivalency.get(target, {}).get('equivalents', (target, ))
        error_object = {'type': type, 'message': message}
        for target in equivalent_targets:
            self.errors[target] = error_object
