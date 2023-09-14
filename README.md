# rtb_argparse

## Installation

```bash
git clone git@github.com:trtb/rtb_argparse.git
cd rtb_argparse/
pip install .
```

## config module: introduction

`rtb_argparse.config` implements the `ArgparseConfig` class, which is the heart of rtb_argparse. It adds a 
`file_parser` argument to argparse which defines a parser for the files given as arguments 
via the `fromfile_prefix_chars` parameter.

The parser must be a function that takes a file name as input, and returns a list of strings as output. For example, 
you can easily create a parser for simple json files: 

```python
import json

def json_file_parser(arg_string):
    with open(arg_string[1:]) as json_file:
        content = json.load(json_file)
    
    ret_strings = []
    for k, values in content.items():
        ret_strings.append(k)
        for v in values if isinstance(values, list) else [values]:
            ret_strings.append(str(v))
    return ret_strings
```

To use it, simply give it as an argument to our parser:

```python
from trtb_argparse.config import ArgparseConfig
parser = ArgparseConfig(fromfile_prefix_chars='@', file_parser=json_file_parser)
```

We can then declare our parser as we usually do with argparse and finally test it:

- test.jon:
```json
{
   "--numbers": [0, 1, 2, 3],
   "--fii": "world!"
}
```

```python
parser.add_argument('--foo', type=str)
parser.add_argument('--numbers', type=int, nargs='+')
parser.add_argument('--fii', type=str)
opt = parser.parse_args(["--foo", "hello", "@test.json"])
print(opt.foo, opt.fii, opt.numbers)
>> hello world! [0, 1, 2, 3]
```

## config module: choose your configuration

The advantage of defining the parsing function yourself is that you can pass parameters to it through the argument you 
give it as input. One example is the `config.json_config_parser` parser, which lets you select a sub-configuration in a 
json file:

- test.json
```json
[
  "text",
  {"--foo":  "foo"},
  {
    "@default": {
      "--conf": "default",
      "--fii": "fii"
    },
    "@conf1": {
      "--conf": "conf1",
      "--fii": "conf1_fii"
    }
  }
]
```

```python
print(json_config_parser("@test.json"))
>> ['text', '--foo', 'foo', '--conf', 'default', '--fii', 'fii']
print(json_config_parser("@test.json@conf1"))
>> ['text', '--foo', 'foo', '--conf', 'conf1', '--fii', 'conf1_fii']
```

## config module: implemented parsers

- `config.default_file_parser`:

This parser reuses the traditional argparse code for reading arguments from a file, modifying the 
`convert_arg_line_to_args` function so that it splits arguments on spaces (default behavior) but also on new lines.
This is the default parser used by the class `ArgparseConfig`.

### Config

The idea behind `config` parsers is to allow you to specify a particular configuration to be read from data files via 
the `fromfile_prefix_chars` option of argparse.  
When you enter the file name in the command line, you can specify one or more configurations using the `prefix_chars` 
character (if not specified, it defaults to `fromfile_prefix_chars`), for example: `@myfile@config1@config3`.

If no configuration is specified, the parser will return the arguments declared outside configurations, and possibly 
those of the `default` configuration if this one is specified in the file.

- `config.config_parser`

Here we start with the same logic as for `config.default_file_parser`, but we are adding the possibility of specifying 
configurations via an argument. A configuration in the file is declared when a line begins with the `prefix_chars` 
character followed by the configuration name, for example: `@conf1 arg1 arg2 \n arg3 ...`. You then remain in this 
configuration until you reach a new one.

```txt
arg0
--arg arg1

@default arg2_default
arg3_default

@conf1 arg2_conf1 -v
```

- `config.json_config_parser`: 

This is a parser for the json format which transforms all file data into string arguments.

Configurations are declared in the json by a key / value pair, where the key is `<prefix_chars><config_name>`, for
example: `"@config1": ... `. Any data outside a configuration will be used, and any data in one of the configurations 
given as an argument will also be used. Data in an unspecified configuration will therefore be ignored.

```json
[
  "text",
  {"--foo":  "foo"},
  {
    "@default": {
      "--conf": "default",
      "--fii": "fii"
    },
    "@conf1": {
      "--conf": "conf1",
      "--fii": "conf1_fii"
    }
  }
]
```

## formatters

Argparse formatters provided by the library:

- `formaters.ArgumentDefaultsHelpFormatter`: 

Modification of the argparse.ArgumentDefaultsHelpFormatter, it displays the default value of each option even if an 
option does not have a help string.

- `formaters.Formatter`:
Derived from `formaters.ArgumentDefaultsHelpFormatter`, `argparse.RawDescriptionHelpFormatter` 
and `argparse.RawTextHelpFormatter`.

## checkers

When adding an argument to argparse, it is common to use a lambda through the `type` parameter of `add_argrument` to 
evaluate the argument given as input. Checkers are simply a set of functions that can be used in these lambdas to 
check arguments at the parsing stage. Among other things, they can be used to specify constraints on numbers, to 
standardize inputs (useful for paths, for example) or to evaluate strings as other objects. 

Examples:
```python
import argparse
from rtb_argparse import checkers

parser = argparse.ArgumentParser()

# Test if x >= 0
parser.add_argument('var1', type=lambda x: checkers.check_superior(x, 0))
# Test if x is a file and if its extension is txt
parser.add_argument('var2', type=lambda x: checkers.check_file_extension(checkers.check_is_file(x), 'txt'))
# Eval the x string with ast.literal_eval and test if the result is a dict
parser.add_argument('var3', type=lambda x: checkers.check_type(checkers.do_literal_eval(x), dict))
```
