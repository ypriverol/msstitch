#!/usr/bin/python3
# FIXME docstring wrong
"""
-- Creating and modifying peptide tables

USAGE:
   peptable.py [option] [input files]
EXAMPLE:
   peptable.py -c psm2pep -i psms.tsv -d /data -o peptides.tsv
"""

import argparse
import os
import app.drivers.peptable.psmtopeptable as psm2pepdrivers


def parser_file_exists(currentparser, fn):
    if not os.path.exists(fn):
        currentparser.error('Input file %s not found!' % fn)
    else:
        return fn


def parser_value_in_list(currentparser, value, valuelist):
    if not value in valuelist:
        currentparser.error('Value {0} should be one of {1}'.format(
            value,
            ', '.join(valuelist)))
    else:
        return value


parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-c', dest='command', type=str,
                    help='How to manipulate the input:\n'
                    'psm2pep - Create peptide table from PSM TSV input,\n'
                    'uses best scoring PSM for each peptide and medians of\n'
                    'quant information. Use with --spectracol, --scorecol,\n'
                    '--ms1quantcolpattern, --isobquantcolpattern.\n\n'
                    '',
                    required=True
                    )
parser.add_argument('-i', dest='infile', help='TSV table containing PSMs or '
                    'peptides',
                    type=lambda x: parser_file_exists(parser, x),
                    required=True)
parser.add_argument('-d', dest='outdir', required=True,
                    help='Directory to output in',
                    type=lambda x: parser_file_exists(parser, x))
#parser.add_argument('--confidence-better', dest='conftype', help='Confidence '
#                    'type to define if higher or lower score is better. One '
#                    'of [higher, lower]',
#                    type=lambda x: parser_value_in_list(parser, x, ['higher',
#                                                                    'lower']))
parser.add_argument('--spectracol', dest='speccol', help='Column number\n'
                    'in which spectra file names are, in case some framework\n'
                    'has changed the file names. First column number and\n'
                    'default is 1.',
                    type=int, required=False)
parser.add_argument('--scorecol', dest='scorecol', help='Column number in '
                    'which score to filter on is written.',
                    type=int, required=False)
parser.add_argument('--ms1quantcolpattern', dest='precursorquantcolpattern',
                    help='Unique text pattern to identify precursor quant \n'
                    'column in PSM table for peptide quanting.',
                    type=str, required=False)
parser.add_argument('--isobquantcolpattern', dest='quantcolpattern',
                    help='Unique text pattern to identify isobaric quant \n'
                    'column in PSM table for peptide quant.',
                    type=str, required=False)
#parser.add_argument('--dbfile', dest='lookup', help='Lookup database in '
#                    'SQLite format, to be created using mslookup.py.',
#                    type=lambda x: parser_file_exists(parser, x))
#parser.add_argument('--unroll', dest='unroll', help='Flag. The tsv input file '
#                    'from Mzid2TSV contains either one PSM per line with all '
#                    'the proteins of that shared peptide on the same line (not'
#                    ' unrolled, default), or one PSM/protein match per line '
#                    'where each protein from that shared peptide gets its own '
#                    'line (unrolled).',
#                    action='store_const', const=True, default=False)
#parser.add_argument('--bioset', dest='bioset', help='Flag. When using '
#                    'splittsv, this enables automatic splitting on '
#                    'biological set names, for which a a column specifying '
#                    'these must exist.',
#                    action='store_const', const=True, default=False)
#parser.add_argument('--splitcol', dest='splitcol', help='Column number on '
#                    'which to split a TSV PSM table', type=int, required=False)
#parser.add_argument('--rename-cols', dest='renamecols', help='Column numbers '
#                    'to rename with name of e.g. set used for splitting. '
#                    'Rename pattern: setname_oldcolumnname.', type=int,
#                    nargs='+')
#parser.add_argument('--rename-col-startswith', dest='renamecolpattern',
#                    help='Rename column headings that start with the pattern '
#                    'specified here. Renaming is done as follows: '
#                    'setname_oldcolumnname.')


# not supported yet
#parser.add_argument('--allpsms', dest='allpsms', action='store_true',
#                    help='All PSMs from a single scan should be included, '
#                    'not only the best scoring one.')

args = parser.parse_args()

commandmap = {
    'psm2pep': psm2pepdrivers.MzidTSVPeptableDriver,
}

command = commandmap[args.command](**vars(args))
command.run()