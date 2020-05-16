# QuickParse
Simple command line argument parser for Python

## Example

list_things.py:
```python
from quickparse import QuickParse

def list_things(a_list, quickparse):
    print(', '.join(map(str, a_list[:quickparse.numeric])))

commands_config = {
    'ls': list_things,
    '': lambda: print(f"Unknown command"),
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
- definition of equivalent options > ('-l', '-L', '--list')
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
`-`: if it comes in place of a value for an option the value becomes None, otherwise it's added as a parameter

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
Make the parser aware that '-s' expects a value (other than `bool`)

### Make the parser aware that an option expects a value after a space
Add type explicitly in `options_config`.
For just getting as it is add `str`.

### How to define option types
Use build-in types like `int` or `float`, or create a callable that raises exceptions.
Using `bool` is a special case: parser will not expect a value but adds an error if one provided.

## Error handling
If the parser parameters 'commands_config' or 'options_config' are not valid, ValueError is rased from the underlying AssertionError.
If the arguments are not compliant with the config (e.g. no value provided for an option that requires one) then no exceptions are raised but an `errors` list is populated on the `QuickParse` object.

TODO: simplified git/chmod

# Supported argument setups
[command] [subcommand]  $ git log
[command] [single-char option]  $ ps -e
[command] [single-char option block]  $ ps -ef
[command] [single-char plus option] [parameter]  $ chmod +x myfile
[command] [double-minus option]  $ git --version
[command] [numeric flag]  $ ps -123
[command] [subcommand] [numeric option]  $ git log -42
[command] [parameter]  $ ls /home
[command] [double-minus key-value]  $ git log --diff-filter=M
[command] [single-minus key-nodelimiter-value]  $ git log -Smytext

subcommand vs parameter: subcommands are validated against an enumerate

# How to define flags
('-u', '--utc') : single-char flag and the equivalent double-minus flag
('-u', '--utc', '--universal') : single-char flag and multiple equivalent double-minus flag

set up valueless flags - that means the next value is a parameter
curl -O http://www.gnu.org/software/gettext/manual/gettext.html

make sure right argument order:
chmod +x myfile

value can be '-'
curl -C - -O http://www.gnu.org/software/gettext/manual/gettext.html
