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

## GNU Argument Syntax implementation with extensions
GNU Argument Syntax: https://www.gnu.org/software/libc/manual/html_node/Argument-Syntax.html

### Extensions
- numeric flags > -12
- '+' numeric flags > +12
- custom single '-' options
- default single '+' options
- definition of equivalent options - like ('-l', '--list')
- command-subcommand hierarchy
- binding functions to commands

## Argument formats
`-<number>`
`+<number>`
`-<single letter>`
`+<single letter>`
`-<single letter><value>`
`+<single letter><value>`
`-<single letter>=<value>`
`+<single letter>=<value>`
`-<letters>`
`+<letters>`
`-<letters>=<value>`
`+<letters>=<value>`
`--<letters>`
`--<letters>=<value>`
`--`: parameters delimiter - after this everything is added as a parameter

Fine print:
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
