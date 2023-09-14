import argparse


class ArgumentDefaultsHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """
    Modification of the argparse ArgumentDefaultsHelpFormatter:
    Displays the default value of each option even if an option does not have a help string.
    """

    def _format_action(self, action):
        # determine the required width and the entry label
        help_position = min(self._action_max_length + 2,
                            self._max_help_position)
        help_width = max(self._width - help_position, 11)
        action_width = help_position - self._current_indent - 2
        action_header = self._format_action_invocation(action)

        # Code for default if no help
        only_default = False
        if not action.help and action.default is not argparse.SUPPRESS:
            action.help = " "
            only_default = True

        # no help; start on same line and add a final newline
        if not action.help:
            tup = self._current_indent, '', action_header
            action_header = '%*s%s\n' % tup

        # short action name; start on the same line and pad two spaces
        elif len(action_header) <= action_width:
            tup = self._current_indent, '', action_width, action_header
            action_header = '%*s%-*s  ' % tup
            indent_first = 0

        # long action name; start on the next line
        else:
            tup = self._current_indent, '', action_header
            action_header = '%*s%s\n' % tup
            indent_first = help_position

        # collect the pieces of the action help
        parts = [action_header]

        if action.help:  # Remove strip test
            # if there was help for the action, add lines of help text
            help_text = self._expand_help(action)

            # Code for default if no help
            if only_default:  # Remove trailing space at the beginning
                help_text = help_text[2:]

            if help_text:
                help_lines = self._split_lines(help_text, help_width)
                parts.append('%*s%s\n' % (indent_first, '', help_lines[0]))
                for line in help_lines[1:]:
                    parts.append('%*s%s\n' % (help_position, '', line))

        # or add a newline if the description doesn't end with one
        elif not action_header.endswith('\n'):
            parts.append('\n')

        # if there are any sub-actions, add their help as well
        for subaction in self._iter_indented_subactions(action):
            parts.append(self._format_action(subaction))

        # return a single string
        return self._join_parts(parts)


class Formatter(ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter,
                argparse.RawDescriptionHelpFormatter):
    """ Formatter with ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter and RawTextHelpFormatter """
    pass
