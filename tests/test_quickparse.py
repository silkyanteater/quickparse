import pytest

from quickparse import QuickParse


func_names = \
    ['show_help', 'user_list', 'user_add', 'user_del', 'user_select', 'stage_show', 'stage_drop', 'branch_getall', 'branch_add'] + \
    ['branch_move', 'branch_remove', 'import_space', 'export_all', 'export_trees', 'export_gems']
for item in func_names:
    globals()[item] = (lambda s: lambda: s)(item)
    globals()[item].__qualname__ = item


def test_basics():
    with pytest.raises(ValueError):
        cli_args = ['', 'lorem', ()]
        parsed = QuickParse(cli_args=cli_args)
    cli_args = []
    parsed = QuickParse(cli_args=cli_args)
    assert isinstance(parsed.args, (list, tuple))
    assert tuple(parsed.args) == tuple(cli_args)
    assert parsed.commands_config is None
    assert parsed.options_config is None
    assert isinstance(parsed.commands, (list, tuple))
    assert isinstance(parsed.parameters, (list, tuple))
    assert isinstance(parsed.options, dict)
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert callable(parsed.execute)

def test_default_processing_single_parameter():
    cli_args = ['x']
    parsed = QuickParse(cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == ('x', )
    assert tuple(parsed.options) == tuple()
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0

def test_default_processing_numerics():
    cli_args = '-12 +12'.split()
    parsed = QuickParse(cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert tuple(parsed.options) == tuple()
    assert parsed.numeric == 12
    assert parsed.plusnumeric == 12
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0

def test_stacked_processing_numerics():
    cli_args = '-11 -12'.split()
    parsed = QuickParse(cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert tuple(parsed.options) == tuple()
    assert parsed.numeric == (11, 12)
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0
    cli_args = '+11 +12 -13'.split()
    parsed = QuickParse(cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert tuple(parsed.options) == tuple()
    assert parsed.numeric == 13
    assert parsed.plusnumeric == (11, 12)
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0

def test_default_processing_unpacking():
    cli_args = ['-abc']
    parsed = QuickParse(cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'-a': True, '-b': True, '-c': True}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0

def test_stacked_processing_unpacking():
    cli_args = '-abc -xyz'.split()
    parsed = QuickParse(cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'-a': True, '-b': True, '-c': True, '-x': True, '-y': True, '-z': True}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0
    cli_args = '-abc -abc'.split()
    parsed = QuickParse(cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'-a': (True, True), '-b': (True, True), '-c': (True, True)}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0

def test_double_processing_unpacking():
    cli_args = ['-abc', '-def']
    parsed = QuickParse(cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'-a': True, '-b': True, '-c': True, '-d': True, '-e': True, '-f': True}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0

def test_default_processing_no_unpacking():
    cli_args = ['-abc-d']
    parsed = QuickParse(cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'-abc-d': True}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0

def test_default_processing_minus_key_value():
    cli_args = ['-abc=xyz']
    parsed = QuickParse(cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'-abc': 'xyz'}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0

def test_default_processing_doubleminus_key_value():
    cli_args = ['--abc=xyz']
    parsed = QuickParse(cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'--abc': 'xyz'}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0

def test_options_config_no_unpacking():
    options_config = [
        ('-abc', ),  # says not to unpack it
    ]
    cli_args = ['-abc']
    parsed = QuickParse(options_config=options_config, cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'-abc': True}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0

def test_options_config_equivalents():
    options_config = [
        ('-a', '--all'),
    ]
    cli_args = ['-a']
    parsed = QuickParse(options_config=options_config, cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'-a': True, '--all': True}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0

def test_options_config_unpacking_with_value():
    options_config = [
        ('-x', '--extra', int),
    ]
    cli_args = ['-xyz', '8']
    parsed = QuickParse(options_config=options_config, cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == (8, )
    assert parsed.options == {'-x': 'yz', '--extra': 'yz'}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 1
    cli_args = ['-yxz']
    parsed = QuickParse(options_config=options_config, cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'--extra': True, '-x': True, '-y': True, '-z': True}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 1
    cli_args = ['-yxz', '8']
    parsed = QuickParse(options_config=options_config, cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'--extra': 8, '-x': 8, '-y': True, '-z': True}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0
    cli_args = ['-yzx', '8']
    parsed = QuickParse(options_config=options_config, cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'-x': 8, '--extra': 8, '-y': True, '-z': True}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0

def test_options_config_equivalent_key_values():
    options_config = [
        ('-n', '-name', '--name', str),
    ]
    cli_args = ['-nFoo']
    parsed = QuickParse(options_config=options_config, cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'-n': 'Foo', '-name': 'Foo', '--name': 'Foo'}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0
    cli_args = ['-n', 'Foo']
    parsed = QuickParse(options_config=options_config, cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'-n': 'Foo', '-name': 'Foo', '--name': 'Foo'}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0
    cli_args = ['-n=Foo']
    parsed = QuickParse(options_config=options_config, cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'-n': 'Foo', '-name': 'Foo', '--name': 'Foo'}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0
    cli_args = ['-name', 'Foo']
    parsed = QuickParse(options_config=options_config, cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'-n': 'Foo', '-name': 'Foo', '--name': 'Foo'}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0
    cli_args = ['-name=Foo']
    parsed = QuickParse(options_config=options_config, cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'-n': 'Foo', '-name': 'Foo', '--name': 'Foo'}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0
    cli_args = ['-name']
    parsed = QuickParse(options_config=options_config, cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'-n': True, '-name': True, '--name': True}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 1
    cli_args = ['-name=']
    parsed = QuickParse(options_config=options_config, cli_args=cli_args)
    assert tuple(parsed.commands) == tuple()
    assert tuple(parsed.parameters) == tuple()
    assert parsed.options == {'-n': '', '-name': '', '--name': ''}
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == None
    assert len(parsed.errors) == 0

options_config = [
    ('-l', '--long', bool),  # adds an error if a value is provided using '='
]

commands_config_ok = {
    ('help', 'h'): show_help,
    'user': {
        '': user_select,
        'ls': user_list,
        'add': user_add,
        'del': user_del,
    },
    ('stage', 'st'): {
        '': stage_show,
        'drop': stage_drop,
    },
    ('branch', 'br'): {
        '': branch_getall,
        'add': branch_add,
        ('move', 'mv'): branch_move,
        ('delete', 'del'): branch_remove,
    },
    ('import', 'im'): import_space,
    ('export', 'ex'): {
        '': export_all,
        ('tree', 'tr'): export_trees,
        ('gem', ): export_gems,
    },
}

def test_basics_with_configs():
    cli_args = []
    parsed = QuickParse(commands_config_ok, options_config, cli_args=cli_args)
    assert isinstance(parsed.args, (list, tuple))
    assert tuple(parsed.args) == tuple(cli_args)
    assert isinstance(parsed.commands_config, dict)
    assert parsed.commands_config == commands_config_ok
    assert isinstance(parsed.options_config, (list, tuple))
    assert parsed.options_config == options_config
    assert isinstance(parsed.commands, (list, tuple))
    assert isinstance(parsed.parameters, (list, tuple))
    assert isinstance(parsed.options, dict)
    assert isinstance(parsed.non_commands, (list, tuple))
    assert callable(parsed.execute)

def test_commands_config_ok():
    cli_args = ['h']
    parsed = QuickParse(commands_config_ok, cli_args=cli_args)
    assert len(parsed.commands) == 2 and 'h' in parsed.commands and 'help' in parsed.commands
    assert len(parsed.parameters) == 0
    assert len(parsed.non_commands) == 0
    assert parsed.execute() == 'show_help'
    assert parsed.execute('lorem') == 'show_help'

def test_commands_config_dupe_keys():
    commands_config_dupe_keys = {
        ('help', 'h'): show_help,
        ('stage', 'st', 'h'): stage_show,
    }
    with pytest.raises(ValueError):
        cli_args = ['h']
        parsed = QuickParse(commands_config_dupe_keys, cli_args=cli_args)

def test_parameters():
    cli_args = 'user add user1'.split()
    parsed = QuickParse(commands_config_ok, cli_args=cli_args)
    assert tuple(parsed.commands) == ('user add', )
    assert set(parsed.parameters) == {'user1'}
    assert set(parsed.non_commands) == {'user1'}
    assert parsed.options == dict()
    assert parsed.numeric == None
    assert parsed.plusnumeric == None
    assert parsed.to_execute == user_add
    assert len(parsed.errors) == 0

def test_non_commands():
    cli_args = 'user add user1 -3 --list'.split()
    parsed = QuickParse(commands_config_ok, cli_args=cli_args)
    assert tuple(parsed.commands) == ('user add', )
    assert set(parsed.parameters) == {'user1'}
    assert set(parsed.non_commands) == {'user1', '-3', '--list'}
    assert parsed.options == {'--list': True}
    assert parsed.numeric == 3
    assert parsed.plusnumeric == None
    assert parsed.to_execute == user_add
    assert len(parsed.errors) == 0
