#
# statistics.py
#
#  Copyright (C) 2013 Diamond Light Source
#
#  Author: James Parkhurst
#
#  This code is distributed under the BSD license, a copy of which is
#  included in the root directory of this package.
from __future__ import division
from dials.array_family import flex
from dials.array_family.flex import Binner


class ImageSummary(object):
  ''' A class to produce statistics per image. '''

  def __init__(self, data, experiment):
    ''' Compute stats. '''

    # Check some table columns
    assert("bbox" in data)
    assert("partiality" in data)
    assert("intensity.sum.value" in data)
    assert("intensity.sum.variance" in data)

    # Get the array range
    try:
      array_range = experiment.imageset.get_array_range()
    except:
      array_range = (0, len(experiment.imageset))

    # Get arrays for each frame
    data = data.select(data.get_flags(data.flags.integrated, all=False))
    data.split_partials()
    frames = data['bbox'].parts()[4]

    # Create the binner with the bins per image
    binner = Binner(flex.int(range(
      array_range[0],
      array_range[1]+1)).as_double())

    # Get the bins
    self.bins = binner.bins()

    # Get full and partial counts
    full = data['partiality'] > 0.997300203937
    bin_indexer = binner.indexer(frames.as_double())
    self.full = bin_indexer.sum(full.as_double())
    self.part = bin_indexer.sum((~full).as_double())

    # Get stuff from table for summation
    i_sum_flg = data.get_flags(data.flags.integrated_sum)
    i_sum_val = data['intensity.sum.value'].select(i_sum_flg)
    i_sum_var = data['intensity.sum.variance'].select(i_sum_flg)
    assert(i_sum_var.all_gt(0))
    ios_sum = i_sum_val / flex.sqrt(i_sum_var)
    bin_indexer = binner.indexer(frames.select(i_sum_flg).as_double())
    self.num_sum = bin_indexer.count()
    self.ios_sum = bin_indexer.mean(ios_sum)

    # Get stuff from table for profile fitting
    try:
      i_prf_flg = data.get_flags(data.flags.integrated_prf)
      i_prf_val = data['intensity.prf.value'].select(i_prf_flg)
      i_prf_var = data['intensity.prf.variance'].select(i_prf_flg)
      assert(i_prf_var.all_gt(0))
      ios_prf = i_prf_val / flex.sqrt(i_prf_var)
      bin_indexer = binner.indexer(frames.select(i_prf_flg).as_double())
      self.num_prf = bin_indexer.count()
      self.ios_prf = bin_indexer.mean(ios_prf)
    except RuntimeError:
      self.num_prf = flex.size_t(len(self.bins), 0)
      self.ios_prf = flex.size_t(len(self.bins), 0)

  def __len__(self):
    ''' The number of bins. '''
    assert(len(self.bins) > 1)
    return len(self.bins)-1

  def table(self):
    ''' Produce a table of results. '''
    from libtbx.table_utils import format as table
    rows = [["Image",
             "# full",
             "# part",
             "# sum",
             "# prf",
             "<I/sigI>\n (sum)",
             "<I/sigI>\n (prf)"]]
    for i in range(len(self)):
      rows.append([
        '%d' % self.bins[i],
        '%d' % self.full[i],
        '%d' % self.part[i],
        '%d' % self.num_sum[i],
        '%d' % self.num_prf[i],
        '%.1f' % self.ios_sum[i],
        '%.1f' % self.ios_prf[i]])
    return table(rows, has_header=True, justify='right', prefix=' ')


class ResolutionSummary(object):
  ''' A class to produce statistics in resolution shells. '''

  def __init__(self, data, experiment, nbins=10):
    ''' Compute the statistics. '''
    from cctbx import miller
    from cctbx import crystal

    # Check some table columns
    assert("d" in data)
    assert("intensity.sum.value" in data)
    assert("intensity.sum.variance" in data)

    # Select integrated reflections
    data = data.select(data.get_flags(data.flags.integrated, all=False))

    # Create the crystal symmetry object
    cs = crystal.symmetry(
      space_group=experiment.crystal.get_space_group(),
      unit_cell=experiment.crystal.get_unit_cell())

    # Create the array of bins
    ms = miller.set(cs, data['miller_index'])
    ms.setup_binner(n_bins=nbins)
    binner = ms.binner()
    brange = list(binner.range_used())
    bins = [binner.bin_d_range(brange[0])[0]]
    for i in brange:
      bins.append(binner.bin_d_range(i)[1])
    bins = flex.double(reversed(bins))

    # Create the binner
    binner = Binner(bins)

    # Get the bins
    self.bins = binner.bins()

    # Get full and partial counts
    full = data['partiality'] > 0.997300203937
    bin_indexer = binner.indexer(data['d'])
    self.num_full = bin_indexer.sum(full.as_double())
    self.num_part = bin_indexer.sum((~full).as_double())

    # Get stuff from table for summation
    i_sum_flg = data.get_flags(data.flags.integrated_sum)
    i_sum_val = data['intensity.sum.value'].select(i_sum_flg)
    i_sum_var = data['intensity.sum.variance'].select(i_sum_flg)
    assert(i_sum_var.all_gt(0))
    ios_sum = i_sum_val / flex.sqrt(i_sum_var)
    bin_indexer = binner.indexer(data['d'].select(i_sum_flg))
    self.num_sum = bin_indexer.count()
    self.ios_sum = bin_indexer.mean(ios_sum)

    # Get stuff from table for profile fitting
    try:
      i_prf_flg = data.get_flags(data.flags.integrated_prf)
      i_prf_val = data['intensity.prf.value'].select(i_prf_flg)
      i_prf_var = data['intensity.prf.variance'].select(i_prf_flg)
      assert(i_prf_var.all_gt(0))
      ios_prf = i_prf_val / flex.sqrt(i_prf_var)
      bin_indexer = binner.indexer(data['d'].select(i_prf_flg))
      self.num_prf = bin_indexer.count()
      self.ios_prf = bin_indexer.mean(ios_prf)
    except Exception:
      self.num_prf = flex.size_t(len(bins)-1, 0)
      self.ios_prf = flex.double(len(bins)-1, 0)

  def __len__(self):
    ''' The number of bins. '''
    assert(len(self.bins) > 1)
    return len(self.bins)-1

  def table(self):
    ''' Produce a table. '''
    from libtbx.table_utils import format as table
    rows = [["d min",
             "d max",
             "# full",
             "# part",
             "# sum",
             "# prf",
             "<I/sigI>\n (sum)",
             "<I/sigI>\n (prf)"]]
    for i in range(len(self)):
      rows.append([
        '%.1f' % self.bins[i],
        '%.1f' % self.bins[i+1],
        '%d'   % self.num_full[i],
        '%d'   % self.num_part[i],
        '%d'   % self.num_sum[i],
        '%d'   % self.num_prf[i],
        '%.1f' % self.ios_sum[i],
        '%.1f' % self.ios_prf[i]])
    return table(rows, has_header=True, justify='right', prefix=' ')


class WholeSummary(object):
  ''' A class to produce statistics for the whole dataset. '''

  def __init__(self, data, experiment):
    ''' Compute the results. '''

    # Compute for summation
    flags_sum = data.get_flags(data.flags.integrated_sum)
    I_sum_val = data['intensity.sum.value'].select(flags_sum)
    I_sum_var = data['intensity.sum.variance'].select(flags_sum)
    assert(I_sum_var.all_gt(0))
    self.sum_ios = flex.mean(I_sum_val / flex.sqrt(I_sum_var))

    # Compute for profile fitting
    try:
      flags_prf = data.get_flags(data.flags.integrated_prf)
      I_prf_val = data['intensity.prf.value'].select(flags_prf)
      I_prf_var = data['intensity.prf.variance'].select(flags_prf)
      assert(I_prf_var.all_gt(0))
      self.prf_ios = flex.mean(I_prf_val / flex.sqrt(I_prf_var))
    except Exception:
        self.prf_ios = 0.0

  def table(self):
    ''' Produce a table of results. '''
    from libtbx.table_utils import format as table
    rows = [["<I/sigI>\n (sum)",
             "<I/sigI>\n (prf)"]]
    rows.append([
      '%.1f' % self.sum_ios,
      '%.1f' % self.prf_ios])
    return table(rows, has_header=True, justify='right', prefix=' ')


class Summary(object):
  ''' A class to present a summary of integration results. '''

  def __init__(self, data, experiment):
    ''' Initialise. '''
    self._image_summary = ImageSummary(data, experiment)
    self._resolution_summary = ResolutionSummary(data, experiment)
    self._whole_summary = WholeSummary(data, experiment)

  def __str__(self):
    ''' Return as a string. '''
    from dials.util.command_line import heading
    img_summary = self._image_summary.table()
    res_summary = self._resolution_summary.table()
    who_summary = self._whole_summary.table()
    print '=' * 80
    print ''
    print heading('Summary of integration results')
    print ''
    return (
      '%s\n'
      '\n'
      '%s\n'
      '\n'
      ' Summary of integration results as a function of image number'
      '\n%s\n\n'
      ' Summary of integration results binned by resolution'
      '\n%s\n\n'
      ' Summary of integration results for the whole dataset'
      '\n%s\n'
    ) % ('=' * 80,
         heading('Summary of integration results'),
         img_summary,
         res_summary,
         who_summary)


def statistics(data, experiments):
  ''' Return some simple statistics for a reflection table. '''
  tables = data.split_by_experiment_id()
  assert(len(tables) == len(experiments))
  summaries = []
  for table, experiment in zip(tables, experiments):
    summaries.append(Summary(table, experiment))
  return summaries
