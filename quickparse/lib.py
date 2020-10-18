import inspect
import re
from collections.abc import Sequence


option_key_re = re.compile(r'^(-[a-zA-Z][a-zA-Z\-]*|--[a-zA-Z][a-zA-Z\-]*|\+[a-zA-Z][a-zA-Z\-]*)$')

arg_res_def = (
    ('parameters only separator', r'^--$'),
    ('numeric', r'^[-+]\d+$'),
    ('single letter', r'^[-+][a-zA-Z]$'),
    ('doubleminus option', r'^--[a-zA-Z][a-zA-Z\-]*$'),
    ('option and value', r'^(-|--|\+)[a-zA-Z][a-zA-Z\-]*=.*$'),
    ('long option', r'^[-+][a-zA-Z][a-zA-Z\-]+$'),
    ('potential letter and value', r'^[-+][a-zA-Z].+$'),
    ('param or command', r'.*'),
)
arg_res = tuple(map(lambda x: {'type': x[0], 're': re.compile(x[1])}, arg_res_def))

command_re = re.compile(r'[a-zA-Z_\-]+')


def validate_commands_config(commands_config):
    if commands_config is None:
        return
    _validate_key_instances_and_types(commands_config)

def _validate_key_instances_and_types(commands_config_level):
    all_keys = list()
    for key in commands_config_level:
        if isinstance(key, tuple):
            for key_elem in key:
                if isinstance(key_elem, str):
                    _validate_commands_key(key_elem, all_keys)
                else:
                    raise AssertionError(f"Invalid key in commands config: {key_elem}")
        elif isinstance(key, str):
            assert key != '' or not isinstance(commands_config_level[''], dict), f"Empty key in commands_config can't lead to subcommands"
            _validate_commands_key(key, all_keys)
        else:
            raise AssertionError(f"Invalid key in commands config: {key}")
    for key in commands_config_level:
        if isinstance(commands_config_level[key], dict):
            _validate_key_instances_and_types(commands_config_level[key])

def _validate_commands_key(key, all_keys):
    assert key == '' or command_re.match(key) is not None, f"Only [a-zA-Z_-] characteres are allowed in commands config keys, got this: {key}"
    if key in all_keys:
        raise AssertionError(f"Duplicate key in commands config: {key}")
    else:
        all_keys.append(key)

def validate_options_config(options_config):
    if options_config is None:
        return
    options = list()
    assert isinstance(options_config, (list, tuple)), f"List expedted as options config, got this: {options}"
    for equivalents in options_config:
        assert isinstance(equivalents, (list, tuple)), f"List expedted as options config item, got this {equivalents}"
        validator_count = 0
        for equivalent in equivalents:
            if isinstance(equivalent, str):
                equivalent_stripped = equivalent.strip()
                assert option_key_re.match(equivalent_stripped) is not None , f"Valid option formats: '-*', '--*' or '+*' followed by letters and '-'s not in the first place, got this: {equivalent}"
                assert equivalent_stripped not in options, f"Option name found multiple times in options config: {equivalent_stripped}"
                options.append(equivalent_stripped)
            elif not callable(equivalent):
                raise AssertionError(f"Strings or callable validators are accepted in an options config item, got this: {equivalent}")
            else:
                validator_count += 1
                assert validator_count <= 1, f"More than one validator found here: {equivalents}"

def humblecall(func, *args, **kwargs):
    if not callable(func):
        return func
    args = list(args)
    positional_only_args, positional_or_keyword_args, has_positional_var, keyword_only_args, has_keyword_var = _get_func_signature_data(func)
    missing_args = list()
    if len(positional_only_args) > len(args):
        for extra_poso_arg in positional_only_args[len(args):]:
            if not extra_poso_arg['has_default']:
                missing_args.append(extra_poso_arg['name'])
    matched_args = args[:len(positional_only_args)]
    args = args[len(positional_only_args):]
    for pork_arg in positional_or_keyword_args:
        name = pork_arg['name']
        if name in kwargs:
            matched_args.append(kwargs[name])
            del kwargs[name]
        else:
            if len(args) > 0:
                matched_args.append(args.pop(0))
            elif not pork_arg['has_default']:
                missing_args.append(name)
    keyword_only_arg_names = list()
    for kwo_arg in keyword_only_args:
        name = kwo_arg['name']
        if not kwo_arg['has_default'] and name not in kwargs:
            missing_args.append(name)
        keyword_only_arg_names.append(name)
    if len(missing_args) > 0:
        raise TypeError(f"Arguments for calling {func.__name__}() are missing: {', '.join(missing_args)}")
    if has_positional_var:
        matched_args += args
    if not has_keyword_var:
        kwargs = {key: value for key, value in kwargs.items() if key in keyword_only_arg_names}
    return func(*matched_args, **kwargs)

def _get_func_signature_data(func):
    positional_only_args = list()
    positional_or_keyword_args = list()
    has_positional_var = False
    keyword_only_args = list()
    has_keyword_var = False
    for name, param in inspect.signature(func).parameters.items():
        param_data = {
            'name': name,
            'has_default': param.default is not inspect._empty
        }
        if param.kind == param.POSITIONAL_ONLY:
            positional_only_args.append(param_data)
        elif param.kind == param.POSITIONAL_OR_KEYWORD:
            positional_or_keyword_args.append(param_data)
        elif param.kind == param.VAR_POSITIONAL:
            has_positional_var = True
        elif param.kind == param.KEYWORD_ONLY:
            keyword_only_args.append(param_data)
        elif param.kind == param.VAR_KEYWORD:
            has_keyword_var = True
    return positional_only_args, positional_or_keyword_args, has_positional_var, keyword_only_args, has_keyword_var

def get_arg_type(arg):
    for arg_re in arg_res:
        if arg_re['re'].match(arg) is not None:
            return arg_re['type']
    raise RuntimeError(f"Incomplete regular expression coverage of argument {arg}")

def get_equivalent_commands(commands, commands_config):
    if len(commands) == 0:
        return tuple()
    if commands_config is None:
        return (' '.join(commands), )
    command_equivalents_per_level = list()
    commands_config_level = commands_config
    for command in commands:
        if command in commands_config_level:
            command_equivalents_per_level.append((command, ))
            commands_config_level = commands_config_level[command]
            continue
        for equivalent_group, next_commands_config_level in commands_config_level.items():
            if isinstance(equivalent_group, tuple) and command in equivalent_group:
                command_equivalents_per_level.append(equivalent_group)
                commands_config_level = next_commands_config_level
                break
    permutations = _get_permutations([[]], command_equivalents_per_level)
    return tuple(' '.join(permutation) for permutation in permutations)

def _get_permutations(permutations, items):
    if len(items) == 0:
        return permutations
    new_permutations = list()
    for item in items[0]:
        for permutation in permutations:
            new_permutations.append(permutation + [item])
    return _get_permutations(new_permutations, items[1:])

def get_options_equivalency(options_config):
    if options_config is None:
        return dict()
    options_equivalency = dict()
    for equivalents in options_config:
        option_validator = ([eq for eq in equivalents if callable(eq)] or [None])[0]
        equivalent_options = tuple(eq.strip() for eq in equivalents if isinstance(eq, str))
        equivalency = {'validator': option_validator, 'equivalents': equivalent_options}
        for eq_option in equivalent_options:
            options_equivalency[eq_option] = equivalency
    return options_equivalency

def expand_commands_config_keys(commands_config_level):
    if commands_config_level is None:
        return {'': None}
    expanded_commands_config = dict()
    for key, value in commands_config_level.items():
        if isinstance(key, tuple):
            for key_elem in key:
                expanded_commands_config[key_elem] = value
        else:
            expanded_commands_config[key] = value
    deep_expanded_commands_config = dict()
    for key, value in expanded_commands_config.items():
        if isinstance(value, dict):
            deep_expanded_commands_config[key] = expand_commands_config_keys(value)
        else:
            deep_expanded_commands_config[key] = value
    return deep_expanded_commands_config

def is_non_stringlike_sequence(item):
    return isinstance(item, Sequence) and not isinstance(item, (str, bytes))
