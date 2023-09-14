import sys as _sys
import argparse
import json
from typing import List, Optional, Callable, Generator


""" ArgparseConfig and default_file_parser """


def convert_arg_line_to_args(arg_line: str) -> Generator[str, None, None]:
    # see https://docs.python.org/3.3/library/argparse.html#argparse.ArgumentParser.convert_arg_line_to_args
    for arg in arg_line.split():
        if not arg.strip():
            continue
        yield arg


def default_file_parser(arg_string: str) -> List[str]:
    """
    Opens the file arg_string[1:] and splits the content into arguments (split performed on spaces and line breaks).
    """
    ret_strings = []
    with open(arg_string[1:]) as args_file:
        for arg_line in args_file.read().splitlines():
            for arg in convert_arg_line_to_args(arg_line):
                ret_strings.append(arg)
    return ret_strings


class ArgparseConfig(argparse.ArgumentParser):
    """
    Inherited from the class argparse.ArgumentParser, overwrites the method _read_args_from_files to use
    an exterior function for file parsing.
    """
    def __init__(self, file_parser: Callable[[str], List[str]] = default_file_parser, **kwargs):
        super().__init__(**kwargs)
        self.file_parser = file_parser

    def _read_args_from_files(self, arg_strings):
        # expand arguments referencing files
        new_arg_strings = []
        for arg_string in arg_strings:

            # for regular arguments, just add them back into the list
            if not arg_string or arg_string[0] not in self.fromfile_prefix_chars:
                new_arg_strings.append(arg_string)

            # replace arguments referencing files with the file content
            else:
                try:
                    arg_strings = self.file_parser(arg_string)
                    arg_strings = self._read_args_from_files(arg_strings)
                    new_arg_strings.extend(arg_strings)
                except OSError:
                    err = _sys.exc_info()[1]
                    self.error(str(err))

        # return the modified argument list
        return new_arg_strings


""" Parsers """


class Parser:
    """
    Abstract class for creating parsers.
    """
    def __init__(self, arg_string: str, verbose: bool = False, prefix_chars: Optional[str] = None):
        """
        The idea behind this class is to allow you to specify a particular configuration to be read from data files via
        the `fromfile_prefix_chars` option of argparse.
        When you enter the file name in the command line, you can specify one or more configurations using the
        `prefix_chars` character (if not specified, it defaults to `fromfile_prefix_chars`), for example:
        `@myfile@config1@config3`.

        If no configuration is specified, the parser will return the arguments declared outside configurations,
        and possibly those of the `default` configuration if this one is specified in the file.

        :param arg_string: string given by ArgparseConfig._read_args_from_files
        :param verbose: if true, print filename and config
        :param prefix_chars: string of len 1, if None, use arg_string[0] as prefix_chars
        """
        self.prefix_chars = arg_string[0] if prefix_chars is None else prefix_chars[0]
        self.filename = arg_string[1:]
        self.config_valid = True
        self.config = ["default"]
        self.ret_strings = []

        if self.prefix_chars in self.filename:
            self.filename, *self.config = self.filename.split(self.prefix_chars)
            self.config_valid = False

        if verbose:
            print("Reading args from '{}' with config '{}'".format(self.filename, self.config))

    def get_args(self) -> List[str]:
        """ Test if the required config as been found during parsing and return the result of the parsing """
        if not self.config_valid:
            raise argparse.ArgumentTypeError("Required config: '{}' not found in '{}'".format(self.config,
                                                                                              self.filename))
        return self.ret_strings


class ParserJson(Parser):
    """
    Parse json file using Parser

    Configurations are declared in the json by a key / value pair, where the key is `<prefix_chars><config_name>`, for
    example: `"@config1": ...`. Any data outside a configuration will be used, and any data in one of the configurations
    given as an argument will also be used. Data in an unspecified configuration will therefore be ignored.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            with open(self.filename) as json_file:
                json_content = json.load(json_file)
        except json.decoder.JSONDecodeError:
            raise argparse.ArgumentTypeError("Error while reading json config from '{}'".format(self.filename))

        self.parse_element(json_content)

    def parse_element(self, element):
        """ Parse an element of the json file

        :param element: Could be a dict, a list or a simple type (number, bool, string, none)
        """
        if isinstance(element, dict):
            for k, v in element.items():
                if k[0] == self.prefix_chars:
                    if k[1:].strip() in self.config:
                        self.parse_element(v)
                        self.config_valid = True
                else:
                    self.ret_strings.append(k)
                    self.parse_element(v)
        elif isinstance(element, list):
            for v in element:
                self.parse_element(v)
        else:
            self.ret_strings += [str(element)]


def json_config_parser(arg_string: str, verbose: bool = False, prefix_chars: Optional[str] = None) -> List[str]:
    """ Encapsulate the ParserJson in a simple function.

    :param arg_string: string given by ArgparseConfig._read_args_from_files
    :param verbose: if true, print filename and config
    :param prefix_chars: string of len 1, if None, use arg_string[0] as prefix_chars
    :return: List of arguments (strings)
    """
    return ParserJson(arg_string, verbose=verbose, prefix_chars=prefix_chars).get_args()


class ParserConfig(Parser):
    """
    Parse simple txt file using Parser.

    Same logic as for `config.default_file_parser`, but we are adding the possibility of specifying
    configurations via an argument. A configuration in the file is declared when a line begins with the `prefix_chars`
    character followed by the configuration name, for example: `@conf1 arg1 arg2 \n arg3 ...`. You then remain in this
    configuration until you reach a new one.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        section = None
        with open(self.filename) as config_file:
            for line in filter(None, config_file.read().splitlines()):
                if line[0] == self.prefix_chars:
                    section, line = line[1:].split(" ", 1)
                    section = section.strip()
                    if section in self.config:
                        self.config_valid = True
                if section is None or section in self.config:
                    for arg in convert_arg_line_to_args(line):
                        self.ret_strings.append(arg)


def config_parser(arg_string: str, verbose: bool = False, prefix_chars: Optional[str] = None) -> List[str]:
    """ Encapsulate the ParserConfig in a simple function.

    :param arg_string: string given by ArgparseConfig._read_args_from_files
    :param verbose: if true, print filename and config
    :param prefix_chars: string of len 1, if None, use arg_string[0] as prefix_chars
    :return: List of arguments (strings)
    """
    return ParserConfig(arg_string, verbose=verbose, prefix_chars=prefix_chars).get_args()
