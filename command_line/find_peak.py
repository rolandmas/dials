from __future__ import division
from dxtbx.sweep import SweepFactory
from dials.algorithms.peak_finding.spot_finder_lui import SpotFinderLui
#from dials.scratch.luiso_s.to_dials_reg.func_fnd_pk import *

import numpy
def fnd_pk():
    import sys
    from dxtbx.format.Registry import Registry

    arg_lst = sys.argv[1:]
    algrm = 'none'
    filenames = []
    times = 5
    shift = 10
    n_blocks_x = 5
    n_blocks_y = 12
    for arg in arg_lst:
        if '=' in arg:
            leng_01 = arg.find('=')
            lft_str = arg[:leng_01].lower()
            print lft_str
            if lft_str == 'algr' or lft_str == 'al':
                if arg[leng_01 + 1:] == 'lui':
                    algrm = 'lui'
                else:
                    algrm = 'xds'
            elif lft_str == 'times' or lft_str == 'tm':
                times = int(arg[leng_01 + 1:])
            elif lft_str == 'shf' or lft_str == 'shift':
                shift = int(arg[leng_01 + 1:])
            elif lft_str == 'nbx' or lft_str == 'numblockx':
                n_blocks_x = int(arg[leng_01 + 1:])
            elif lft_str == 'nby' or lft_str == 'numblocky':
                n_blocks_y = int(arg[leng_01 + 1:])

        else:
            filenames.append(arg)
    print len(filenames), "images given"
    print 'following', algrm, 'algorithm'

    print 'algrm =', algrm

    print'___________________________'
    print 'filenames =', filenames

    if algrm == 'none':
        print 'no algorithm spesifyed'
    else:
        if algrm == 'lui':
            sweep = SweepFactory.sweep(filenames)
            find_spots = SpotFinderLui()
            reflection_list = find_spots(sweep, times, shift, n_blocks_x, n_blocks_y)

            import pickle
            output_file = 'lui_reflections.pkl'
            pickle.dump(reflection_list, open(output_file, 'wb'))
        elif algrm == 'xds':
            print 'xds algorithm needs to be connected'

            #from optparse import OptionParser, OptionGroup, IndentedHelpFormatter
            #
            ## Specify the command line options
            #usage = "usage: %prog [options] /path/to/image/files"
            #
            ## Create an option parser
            #parser = OptionParser(usage)
            #
            ## Add algorithm options
            #parser.add_option(
            #    '-t', '--threshold',
            #    dest = 'threshold',
            #    type = 'choice', choices = ['xds', 'unimodal'], default = 'xds',
            #    help = 'The threshold algorithm to use (default = %default)')
            #parser.add_option(
            #    '-o', '--output-file',
            #    dest = 'output_file',
            #    type = 'string', default = None,
            #    help = 'Select a file to save the spots.')
            #
            ## Create a group for threshold options
            #threshold_group = OptionGroup(
            #    parser, 'Threshold Options',
            #    'Options affecting threshold algorithms')
            #threshold_group.add_option(
            #    '--dark-current-file',
            #    dest = 'dark_current_file', type = "string", default = None,
            #    help = 'Dark current map filename')
            #threshold_group.add_option(
            #    '--gain-map-file',
            #    dest = 'gain_map_file', type = "string", default = None,
            #    help = 'Gain map filename')
            #threshold_group.add_option(
            #    '--sigma-background',
            #    dest = 'sigma_background', type = 'float', default = 6.0,
            #    help = '(var/mean) > gain + n_sigma*gain*sqrt(2/(n - 1))')
            #threshold_group.add_option(
            #    '--sigma-strong',
            #    dest = 'sigma_strong', type = 'float', default = 3.0,
            #    help = 'pixel > mean + n_sigma*sdev (used by: xds) (default: %default)')
            #threshold_group.add_option(
            #    '--kernel-size',
            #    dest = 'kernel_size', type = 'int', nargs = 2, default = (3, 3),
            #    help = 'Local window size (2 * s + 1) centred on pixel')
            #
            ## Create group for filter options
            #filter_group = OptionGroup(
            #    parser, 'Filter options',
            #    'Options affecting filter algorithms')
            #filter_group.add_option(
            #    '--min-spot-size',
            #    dest = 'min_spot_size', type = "int", default = 6,
            #    help = 'Minimum pixels in spot')
            #filter_group.add_option(
            #    '--max-pc-separation',
            #    dest = 'max_pc_separation', type = "int", default = 2,
            #    help = 'Maximum peak-centroid distance')
            #
            ## Add the related groups of options
            #parser.add_option_group(threshold_group)
            #parser.add_option_group(filter_group)
            #
            ## Parse the arguments
            #options, args = parser.parse_args()

if __name__ == '__main__':
    fnd_pk()
