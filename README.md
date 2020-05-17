# QuickParse
Simple command line argument parser for Python

## Example

`list_things.py`:
```python
from quickparse import QuickParse

def list_things(a_list, quickparse):
    print(', '.join(map(str, a_list[:quickparse.numeric])))

commands_config = {
    'ls': list_things,
    '': lambda: print(f"Command is missing, use 'ls'"),
}

mylist = list(range(1, 12))

QuickParse(commands_config).execute(mylist)
```

Run it:
```sh
$ python list_things.py ls -5
1, 2, 3, 4, 5
```

The way it works:
- `commands_config` tells QuickParse to look for `ls` as a command and call `list_things` on it - when no commands show help
- QuickParse parses arguments as normal while `ls` is privileged as a command
- QuickParse finds `-5` so it adds as `quickparse.numeric = 5` (`quickparse` being the `QuickParse` instance coming from `QuickParse(commands_config)`)
- QuickParse sees `list_things` being associated to `ls`, so `quickparse.execute(mylist)` calls it, passing down a positional argument
- since `list_things` expects a named argument `quickparse`, QuickParse makes sure it passes down the reference to its own instance of `quickparse`

## GNU Argument Syntax implementation with extensions
GNU Argument Syntax: https://www.gnu.org/software/libc/manual/html_node/Argument-Syntax.html

### Extensions
#### numeric flags
```$ cmd -12```bash
#### '+' numeric flags
```$ cmd +12```bash
#### long custom single '-' options
```$ cmd -list```bash
By default it becomes `-l -i -s -t`, but adding `QuickParse(options_config = [ ('-list', ) ])` will stop unpacking.
#### default single '+' options
```$ cmd +list```bash
#### definition of equivalent options - like ('-l', '--list')
```$ cmd -l```bash
is equivalent to
```$ cmd --list```bash
if adding `QuickParse(options_config = [ ('-l', '--list') ])`
#### command-subcommand hierarchy
#### AND
#### binding functions to commands
Defining a random sample from `git` looks like this:
```python
options_config = [
    ('-a', '--all'),
]

commands_config = {
    '': do_show_help,
    'commit': do_commit,
    'log': do_log,
    'stash': {
        '': do_stash,
        'list': do_stash_list,
    }
}

QuickParse(commands_config, options_config).execute()
```
Commands are called according to commands_config, `do_log` in this case: `$ git log -3`
`do_log` may look like this:
```python
def do_log(quickparse):
    print(logentries[:quickparse.numeric])
```
If there is a named argument in `do_log`'s signature called `quickparse`, the object coming from `QuickParse(commands_config, options_config)` is passed down holding all the results of parsing.
Parsing happens by using the defaults and applying what `options_config` adds to it.

## Argument formats
```
-<number>
```
```
+<number>
```
```
-<single_letter>
```
```
+<single_letter>
```
```
-<single_letter><value>
```
```
+<single_letter><value>
```
```
-<single_letter>=<value>
```
```
+<single_letter>=<value>
```
```
-<letters>
```
```
+<letters>
```
```
-<letters>=<value>
```
```
+<letters>=<value>
```
```
--<letters>
```
```
--<letters>=<value>
```
`--` : parameters delimiter

<letters> means [a-zA-Z] and '-'s not in the first place

### An argument like '-a*' gets unpacked if...
- '-a' is not defined to expect a value
- the '*' part only has letters, not '-' or '='

### How to change the interpretation of `-swing`
It can mean:
`-s -w -i -n -g`
or
`-s wing` / `-s=wing`
Make the parser aware that '-s' expects a `str` value

### Make the parser aware that an option expects a value after a space
Add type explicitly in `options_config`.
For just getting as it is add `str`.

### How to define option types
Use build-in types like `int` or `float`, or create a callable that raises exceptions.
Using `bool` is a special case: parser will not expect a value but adds an error if one provided.

### How to add empty value to an option
`-option=`
Some commands support '-' as empty value:
`curl -C - -O http://domanin.com/`
In this case '-' couldn't be explicitely provided, this is why the syntax with '=' is supported here.

## Error handling
If the parser parameters 'commands_config' or 'options_config' are not valid, ValueError is rased from the underlying AssertionError.
If the arguments are not compliant with the config (e.g. no value provided for an option that requires one) then no exceptions are raised but an `errors` list is populated on the `QuickParse` object.

## How to define options
`options_test.py`:
```python
from quickparse import QuickParse

options_config = [
    ('-u', '--utc', '--universal'),
    ('-l', '--long'),
    ('-n', '--name', str),
]

parsed = QuickParse(options_config=options_config)

print(parsed.options)
```

Run it:
```
$ python options_test.py
{}
$ python options_test.py -u
{'-u': True, '--utc': True, '--universal': True}
$ python options_test.py -ul
{'-u': True, '--utc': True, '--universal': True, '-l': True, '--long': True}
$ python options_test.py -uln
{'-uln': True}
$ python options_test.py -ul -nthe_name
{'-u': True, '--utc': True, '--universal': True, '-l': True, '--long': True, '-n': 'the_name', '--name': 'the_name'}
$ python options_test.py -ul -n the_name
{'-u': True, '--utc': True, '--universal': True, '-l': True, '--long': True, '-n': 'the_name', '--name': 'the_name'}
$ python options_test.py -ul -n=the_name
{'-u': True, '--utc': True, '--universal': True, '-l': True, '--long': True, '-n': 'the_name', '--name': 'the_name'}
$ python options_test.py -ul --name the_name
{'-u': True, '--utc': True, '--universal': True, '-l': True, '--long': True, '--name': 'the_name', '-n': 'the_name'}
$ python options_test.py -ul --name=the_name
{'-u': True, '--utc': True, '--universal': True, '-l': True, '--long': True, '--name': 'the_name', '-n': 'the_name'}
```
`-uln` stopped the parser from unpacking because `-n` expected an input value

## Test your command line arguments
`quickparse_test.py` (committed in the repo):
```python
from pprint import pformat

from quickparse import QuickParse


def do_show_help():
    print('Executing \'do_show_help\'...')

def do_commit():
    print('Executing \'do_commit\'...')

def do_log(quickparse):
    print('Executing \'do_log\'...')

def do_stash():
    print('Executing \'do_stash\'...')

def do_stash_list():
    print('Executing \'do_stash_list\'...')

commands_config = {
    '': do_show_help,
    'commit': do_commit,
    'log': do_log,
    'stash': {
        '': do_stash,
        'list': do_stash_list,
    }
}

options_config = [
    ('-m', '--message', str),
    ('-p', '--patch'),
]


parsed = QuickParse(commands_config, options_config)


print(f'Commands:\n{pformat(parsed.commands)}')
print(f'Parameters:\n{pformat(parsed.parameters)}')
print(f'Options:\n{pformat(parsed.options)}')
print(f'\'-\' numeric argument:\n{pformat(parsed.numeric)}')
print(f'\'+\' numeric argument:\n{pformat(parsed.plusnumeric)}')
print(f'Functions to call:\n{pformat(parsed.to_execute)}')

parsed.execute()
```
