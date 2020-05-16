import pytest

from quickparse import QuickParse


options_config = [
    ('-a', '--all'),
    ('-file', ),  # says not to unpack it
    ('-l', '-long', '--long', bool),  # adds an error if a value is provided using '='
    ('-n', '-name', '--name', str),
]

func_names = \
    ['show_help', 'user_list', 'user_add', 'user_del', 'user_select', 'stage_show', 'stage_drop', 'branch_getall', 'branch_add'] + \
    ['branch_move', 'branch_remove', 'import_space', 'export_all', 'export_trees', 'export_gems']
for item in func_names:
    globals()[item] = (lambda s: lambda: s)(item)

commands_config = {
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

def test_basics():
    with pytest.raises(ValueError):
        cli_args = ['', 'lorem', ()]
        parsed = QuickParse(commands_config, options_config, cli_args=cli_args)
    cli_args = []
    parsed = QuickParse(commands_config, options_config, cli_args=cli_args)
    assert isinstance(getattr(parsed, 'args', None), (list, tuple))
    assert tuple(parsed.args) == tuple(cli_args)
    assert isinstance(getattr(parsed, 'commands_config', None), dict)
    assert parsed.commands_config == commands_config
    assert isinstance(getattr(parsed, 'options_config', None), (list, tuple))
    assert parsed.options_config == options_config
    assert isinstance(getattr(parsed, 'commands', None), (list, tuple))
    assert isinstance(getattr(parsed, 'parameters', None), (list, tuple))
    assert isinstance(getattr(parsed, 'options', None), dict)
    assert callable(getattr(parsed, 'execute', None))

def test_commands_config():
    cli_args = ['h']
    parsed = QuickParse(commands_config, cli_args=cli_args)
    assert len(parsed.commands) == 2 and 'h' in parsed.commands and 'help' in parsed.commands
    assert len(parsed.parameters) == 0
    assert parsed.execute() == 'show_help'
    assert parsed.execute('lorem') == 'show_help'
