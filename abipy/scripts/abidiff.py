#!/usr/bin/env python
from __future__ import unicode_literals, division, print_function, absolute_import

import sys
import os
import argparse

from abipy import abilab

def main():
    def str_examples():
        return """\
Usage example:\n

  abidiff.py struct */*/outdata/out_GSR.nc    => Compare structures in multiple files.
  abidiff.py ebands out1_GSR.nc out2_GSR.nc   => Plot electron bands on a grid.
  abidiff.py gs_scf run1.abo run2.abo         => Compare the SCF cycles in two output files.
  abidiff.py dfpt2_scf                        => Compare the DFPT SCF cycles in two output files.
"""

    def show_examples_and_exit(err_msg=None, error_code=1):
        """Display the usage of the script."""
        sys.stderr.write(str_examples())
        if err_msg:
            sys.stderr.write("Fatal Error\n" + err_msg + "\n")
        sys.exit(error_code)

    # Parent parser for common options.
    copts_parser = argparse.ArgumentParser(add_help=False)
    copts_parser.add_argument('paths', nargs="+", help="List of files to compare")
    copts_parser.add_argument('-v', '--verbose', default=0, action='count', # -vv --> verbose=2
                         help='Verbose, can be supplied multiple times to increase verbosity')
    copts_parser.add_argument('--seaborn', action="store_true", help="Use seaborn settings")

    # Build the main parser.
    parser = argparse.ArgumentParser(epilog=str_examples(), formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-V', '--version', action='version', version="%(prog)s version " + abilab.__version__)
    parser.add_argument('--loglevel', default="ERROR", type=str,
                        help="set the loglevel. Possible values: CRITICAL, ERROR (default), WARNING, INFO, DEBUG")

    # Create the parsers for the sub-commands
    subparsers = parser.add_subparsers(dest='command', help='sub-command help', description="Valid subcommands")

    # Subparser for gs_scf command.
    p_gs_scf = subparsers.add_parser('gs_scf', parents=[copts_parser], help="Compare ground-state SCF cycles.")

    # Subparser for dfpt2_scf command.
    p_dftp2_scf = subparsers.add_parser('dfpt2_scf', parents=[copts_parser], help="Compare DFPT SCF cycles.")

    # Subparser for struct command.
    p_struct = subparsers.add_parser('struct', parents=[copts_parser], help="Compare crystalline structures.")

    # Subparser for ebands command.
    p_ebands = subparsers.add_parser('ebands', parents=[copts_parser], help="Compare electron bands.")

    # Subparser for gsr command.
    #p_gsr = subparsers.add_parser('gsr', parents=[copts_parser], help="Compare electron bands.")

    # Parse the command line.
    try:
        options = parser.parse_args()
    except Exception:
        show_examples_and_exit(error_code=1)

    # loglevel is bound to the string value obtained from the command line argument.
    # Convert to upper case to allow the user to specify --loglevel=DEBUG or --loglevel=debug
    import logging
    numeric_level = getattr(logging, options.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % options.loglevel)
    logging.basicConfig(level=numeric_level)

    if options.seaborn:
        import seaborn as sns
        #sns.set(style="dark", palette="Set2")
        #sns.set(style='ticks', palette='Set2')
        #sns.despine()

    paths = options.paths

    if options.command == "gs_scf":
        f0 = abilab.AbinitOutputFile(paths[0])
        f0.compare_gs_scf_cycles(paths[1:])

    elif options.command == "dfpt2_scf":
        f0 = abilab.AbinitOutputFile(paths[0])
        f0.compare_d2de_scf_cycles(paths[1:])

    elif options.command == "struct":
        index = [os.path.relpath(p) for p in paths]
        frame = abilab.frame_from_structures(paths, index=None)
        print("File list:")
        for i, p in enumerate(paths):
            print("%d %s" % (i, p))
        print()
        print(frame)

    elif options.command == "ebands":
        eb_objects = paths
        titles = paths
        abilab.ebands_gridplot(eb_objects, titles=titles, edos_objects=None, edos_kwargs=None)

    else:
        raise RuntimeError("Don't know what to do with command: %s!" % options.command)

    # Dispatch
    #return globals()["dojo_" + options.command](options)

    return 0


if __name__ == "__main__":
    sys.exit(main())
