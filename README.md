# rtb_argparse

## Introduction

`rtb_argparse` proposes a new class derived from argparse: `ArgparseConfig`. 

This class lets you read arguments from any file format (json, yaml, txt ...) using the `fromfile_prefix_chars` option. 
The only constraint is to define the parser of your file and give it to `ArgparseConfig`.

Through the definition of the file parsing class, the library offers a new way of managing configurations by adding 
the possibility of specifying a sub-configuration to be read from a file with the following syntax: `@myfile@conf1`

The library consists of 3 modules:
- [Config Module](#config-module): `ArgparseConfig` and already defined parser classes for json and txt formats
- [Formatters Module](#formatters-module): New formatters for argparse
- [Checkers Module](#checkers-module): Functions to evaluate the input of an argument threw `type` parameter

## Simple example

To illustrate how `ArgparseConfig` works, here's an example using the `JsonParser()` provided by the library. 
We start by declaring our parser as we're used to with argparse, but including our json parser 
(`file_parser=JsonParser()`):

```python
from rtb_argparse.config import ArgparseConfig, JsonParser

parser = ArgparseConfig(fromfile_prefix_chars="@", file_parser=JsonParser())
parser.add_argument('arg1', type=str)
parser.add_argument("--foo", type=str)
parser.add_argument("--name", type=str)
```

Now let's create a json file and call it `myfile.json`:

```json
[
  "text",
  {
    "--foo": "foo",
    "--name": "myname"
  }
]
```

And the result:

```python
opt = parser.parse_args(["@myfile.json"])
print(opt.arg1, opt.foo, opt.name)
>> text foo myname
```

Since we can define the behaviors we want when parsing the file, we can do a bit more complex things, for example let's 
see what `JsonParser()` can do with this file:

```json
[
  "text",
  {
    "@default": {
      "--foo": "foo",
      "--name": "myname"
    },
    "@conf1": {
      "--foo": "oof",
      "--name": "conf1"
    }
  }
]
```

With `@default` we have declared a default configuration, and with `@conf1` we have declared a second possible 
configuration.

```python
opt = parser.parse_args(["@myfile.json"]) # we do not specify a configuration, so default will be used
print(opt.arg1, opt.foo, opt.name)
>> text foo myname
```

```python
opt = parser.parse_args(["@myfile.json@conf1"]) # by adding @conf1, conf1 will be used instead of default 
print(opt.arg1, opt.foo, opt.name)
>> text oof conf1
```

NB: You can find and test the README.md examples in: [notebooks/readme_examples.ipynb](notebooks/readme_examples.ipynb)

## Installation

- Normal:
```bash
git clone git@github.com:trtb/rtb_argparse.git
cd rtb_argparse/
pip install .
```

- Developer mode:
```bash
git clone git@github.com:trtb/rtb_argparse.git
cd rtb_argparse/
pip install -e .
```

## Config module

### Introduction

`rtb_argparse.config` implements the `ArgparseConfig` class, which is the heart of rtb_argparse. It adds a 
`file_parser` argument to argparse which defines a parser for the files given as arguments 
via the `fromfile_prefix_chars` parameter.

The parser must be a class implementing a method `parse` which takes a file name as input, and returns a list as 
output (string, number ...). The easiest way is to implement a class inheriting from `AbstractParser`, for example 
you can create a parser for simple json files: 

```python
from rtb_argparse.config import AbstractParser
import json

class Parser(AbstractParser):
    def parse(self, arg_string: str):
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

- config_test.json:
```json
{
   "--numbers": [0, 1, 2, 3],
   "--fii": "world!"
}
```

```python
from rtb_argparse.config import ArgparseConfig

parser = ArgparseConfig(fromfile_prefix_chars='@', file_parser=Parser())
parser.add_argument('--foo', type=str)
parser.add_argument('--numbers', type=int, nargs='+')
parser.add_argument('--fii', type=str)
opt = parser.parse_args(["--foo", "hello", "@config_test.json"])

print(opt.foo, opt.fii, opt.numbers)
>> hello world! [0, 1, 2, 3]
```

### Implemented parsers

- `config.DefaultParser`:

This parser reuses the traditional argparse code for reading arguments from a file, using the 
`convert_arg_line_to_args` function so that it splits arguments on spaces.
This is the default parser used by the class `ArgparseConfig`.

### Implemented config parsers

The idea behind `config parsers` is to allow you to specify a particular configuration to be read from data files via 
the `fromfile_prefix_chars` option of argparse.  
When you enter the file name in the command line, you can specify one or more configurations using the `prefix_chars` 
character (if not specified, it defaults to `fromfile_prefix_chars`), for example: `@myfile@config1@config3`.

If no configuration is specified, the parser will return the arguments declared outside configurations, and possibly 
those of the `default` configuration if this one is specified in the file.

- `config.ConfigParser()`

This parser separates incoming file arguments on spaces and line breaks. A configuration in the file is declared when 
a line begins with the `prefix_chars` character followed by the configuration name, 
for example: `@conf1 arg1 arg2 \n arg3 ...`. You then remain in this configuration until you reach a new one.

Example of accepted file:
```txt
arg0
--arg arg1

@default arg2_default
arg3_default

@conf1 arg2_conf1 -v
```

- `config.JsonParser()`: 

This is a parser for the json format which transforms all file data into string arguments.

Configurations are declared in the json by a key / value pair, where the key is `<prefix_chars><config_name>`, for
example: `"@config1": ... `. Any data outside a configuration will be used, and any data in one of the configurations 
given as an argument will also be used. Data in an unspecified configuration will therefore be ignored.

Example of accepted file:
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

## Formatters module

Argparse formatters provided by the library:

- `formaters.ArgumentDefaultsHelpFormatter`: 

Modification of the argparse.ArgumentDefaultsHelpFormatter, it displays the default value of each argument even if an 
argument does not have a help string.

- `formaters.Formatter`:

Derived from `formaters.ArgumentDefaultsHelpFormatter`, `argparse.RawDescriptionHelpFormatter` 
and `argparse.RawTextHelpFormatter`.

## Checkers module

When adding an argument to argparse, it is common to use a lambda through the `type` parameter of `add_argument` to 
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
