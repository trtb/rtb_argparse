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
    def __init__(self, verbose: bool = False, prefix_chars: Optional[str] = None):
        """
        The idea behind this class is to allow you to specify a particular configuration to be read from data files via
        the `fromfile_prefix_chars` option of argparse.
        When you enter the file name in the command line, you can specify one or more configurations using the
        `prefix_chars` character (if not specified, it defaults to `fromfile_prefix_chars`), for example:
        `@myfile@config1@config3`.

        If no configuration is specified, the parser will return the arguments declared outside configurations,
        and possibly those of the `default` configuration if this one is specified in the file.

        :param verbose: if true, print filename and config
        :param prefix_chars: string of len 1, if None, use arg_string[0] as prefix_chars
        """
        self.verbose = verbose
        self.base_prefix_chars = prefix_chars

        # attributes declaration
        self.prefix_chars = ""
        self.filename = ""
        self.config = {}
        self.ret_strings = []

    def _parse(self):
        pass

    def parser(self, arg_string: str) -> List[str]:
        """
        Method to give to ArgparseConfig (file_parser=Parser(...).parser)

        :param arg_string: string given by ArgparseConfig._read_args_from_files
        :return: List of arguments (strings)
        """
        self.prefix_chars = arg_string[0] if self.base_prefix_chars is None else self.base_prefix_chars[0]
        self.filename = arg_string[1:]
        self.config = {"default": True}
        self.ret_strings = []

        if self.prefix_chars in self.filename:
            self.filename, *config = self.filename.split(self.prefix_chars)
            self.config = {c: False for c in config}

        if self.verbose:
            config = ", ".join(list(self.config.keys()))
            print("Reading args from '{}' with config '{}'".format(self.filename, config))

        self._parse()

        if not all(valid for valid in self.config.values()):
            missing = ", ".join([k for k, v in self.config.items() if not v])
            raise argparse.ArgumentTypeError("Required config: '{}' not found in '{}'".format(missing, self.filename))

        return self.ret_strings


class ParserJson(Parser):
    """
    Parse json file using Parser

    Configurations are declared in the json by a key / value pair, where the key is `<prefix_chars><config_name>`, for
    example: `"@config1": ...`. Any data outside a configuration will be used, and any data in one of the configurations
    given as an argument will also be used. Data in an unspecified configuration will therefore be ignored.
    """
    def _parse(self):
        try:
            with open(self.filename) as json_file:
                json_content = json.load(json_file)
        except json.decoder.JSONDecodeError:
            raise argparse.ArgumentTypeError("Error while reading json config from '{}'".format(self.filename))

        self._parse_element(json_content)

    def _parse_element(self, element):
        """ Parse an element of the json file

        :param element: Could be a dict, a list or a simple type (number, bool, string, none)
        """
        if isinstance(element, dict):
            for k, v in element.items():
                if k[0] == self.prefix_chars:
                    config_name = k[1:].strip()
                    if config_name in self.config:
                        self._parse_element(v)
                        self.config[config_name] = True
                else:
                    self.ret_strings.append(k)
                    self._parse_element(v)
        elif isinstance(element, list):
            for v in element:
                self._parse_element(v)
        else:
            self.ret_strings += [str(element)]


class ParserConfig(Parser):
    """
    Parse simple txt file using Parser.

    Same logic as for `config.default_file_parser`, but we are adding the possibility of specifying
    configurations via an argument. A configuration in the file is declared when a line begins with the `prefix_chars`
    character followed by the configuration name, for example: `@conf1 arg1 arg2 \n arg3 ...`. You then remain in this
    configuration until you reach a new one.
    """
    def _parse(self):
        config = None
        with open(self.filename) as config_file:
            for line in filter(None, config_file.read().splitlines()):
                # Remove comment from the file
                line = line.split("#", 1)[0]
                if len(line) == 0:
                    continue

                # Handle config
                if line[0] == self.prefix_chars:
                    config, *tmp_line = line[1:].split(" ", 1)
                    line = tmp_line[0] if len(tmp_line) else ""
                    config = config.strip()
                    if config in self.config:
                        self.config[config] = True

                # Read argument from the config
                if config is None or config in self.config:
                    for arg in convert_arg_line_to_args(line):
                        self.ret_strings.append(arg)
