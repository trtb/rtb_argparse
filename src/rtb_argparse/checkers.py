import argparse
import ast
import os
from numbers import Number


def check_type(value, class_type: type):
    """ assert value is an instance of the given class """
    if not isinstance(value, class_type):
        raise argparse.ArgumentTypeError("Given value {}, is not an instance of {}".format(value, class_type))
    return value


def do_literal_eval(value: str):
    """ apply ast.literal_eval ont the input value """
    try:
        res = ast.literal_eval(value)
    except Exception as e:
        raise argparse.ArgumentTypeError(str(e) + " in " + str(value))
    return res


def check_superior(value: Number, ref: Number):
    """ assert value >= ref"""
    if value < ref:
        raise argparse.ArgumentTypeError("{} is not superior to {}".format(value, ref))
    return value


def check_inferior(value: Number, ref: Number):
    """ assert value <= ref"""
    if value > ref:
        raise argparse.ArgumentTypeError("{} is not inferior to {}".format(value, ref))
    return value


def check_strictly_superior(value: Number, ref: Number):
    """ assert value > ref"""
    if value < ref:
        raise argparse.ArgumentTypeError("{} is not strictly superior to {}".format(value, ref))
    return value


def check_strictly_inferior(value: Number, ref: Number):
    """ assert value < ref"""
    if value < ref:
        raise argparse.ArgumentTypeError("{} is not strictly inferior to {}".format(value, ref))
    return value


def check_between(value: Number, inferior: Number, superior: Number):
    """ assert inferior <= value <= superior """
    if value < inferior or value > superior:
        raise argparse.ArgumentTypeError("{} is not between {} and {}".format(value, inferior, superior))
    return value


def check_strictly_between(value: Number, inferior: Number, superior: Number):
    """ assert inferior < value < superior """
    if value <= inferior or value >= superior:
        raise argparse.ArgumentTypeError("{} is not strictly between {} and {}".format(value, inferior, superior))
    return value


def check_is_file(filename: str) -> str:
    """ assert file path exists """
    if not os.path.isfile(filename):
        raise argparse.ArgumentTypeError("The file {} does not exist".format(filename))
    return filename


def check_is_dir(dirname: str) -> str:
    """ assert file path exists """
    if not os.path.isdir(dirname):
        raise argparse.ArgumentTypeError("The directory {} does not exist".format(dirname))
    return dirname


def check_file_extension(filename: str, ext: str) -> str:
    """ assert path extension is ext (without '.') """
    file_ext = os.path.splitext(filename)[-1][1:]
    if file_ext != ext:
        raise argparse.ArgumentTypeError("Wrong file type {}, expected : {}".format(file_ext, ext))
    return filename


def dir_add_slash(path: str) -> str:
    """ assert path end by a slash, otherwise add as slash """
    if path[-1] != "/":
        path += "/"
    return path


def eval_string(string: str):
    """ apply ast.literal_eval on "\"{}\"".format(string), useful to interpret correctly \n or \t for example """
    string = ast.literal_eval("\"{}\"".format(string))
    if not isinstance(string, str):
        msg = "Given value {} has been interpreted as a {}, expected a {}.".format(string, type(string), str)
        raise argparse.ArgumentTypeError(msg)
    return string