from __future__ import absolute_import, division, print_function
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec
from mpl_toolkits.axes_grid1 import make_axes_locatable
#from cctbx.array_family import flex
from dials.array_family import flex
import sys
from dials.algorithms.scaling import ScalingModelFactory
from dials.algorithms.scaling import Model
from dials.algorithms.scaling.scaling_utilities import parse_multiple_datasets
from libtbx import phil
from dials.util import halraiser
from dials.util.options import OptionParser, flatten_reflections, flatten_experiments

phil_scope = phil.parse('''
  debug = False
    .type = bool
    .help = "Output additional debugging information"
  output {
    scales_out = "scale_model"
      .type = str
      .help = "Option to set filename for output plot."
    absorption_out = "absorption_surface"
      .type = str
      .help = "Option to set filename for output absorption plot."
    experiment_range = ()
      .type = ints
      .help = "Option to specify a subset of experiments to plot."
  }
  include scope dials.algorithms.scaling.scaling_options.phil_scope
''', process_includes=True)

def main(argv):
  '''the plotting script'''

  optionparser = OptionParser(usage=None, read_experiments=True,
    read_reflections=True, read_datablocks=False, phil=phil_scope,
    check_format=False)
  params, _ = optionparser.parse_args(argv, show_diff_phil=False)


  if not params.input.experiments or not params.input.reflections:
    optionparser.print_help()
    return

  diff_phil = optionparser.diff_phil.as_str()
  if diff_phil is not '':
    print('The following parameters have been modified:\n')
    print(diff_phil)

  reflections = flatten_reflections(params.input.reflections)
  experiments = flatten_experiments(params.input.experiments)

  if len(experiments) != 1:
    print(('Checking for the existence of a reflection table containing {sep}'
    'multiple scaled datasets. {sep}').format(sep='\n'))
    reflections = parse_multiple_datasets(reflections)
    print("Found %s experiments in total." % len(experiments))
    print('\n'+'*'*40)

  experiments = ScalingModelFactory.Factory.create(params, experiments, reflections)

  print('\nPlotting graphs of scale factors. \n')
  if len(experiments) == 1:
    if isinstance(experiments[0].scaling_model, Model.AimlessScalingModel):
      plot_smooth_scales(params, experiments[0], reflections[0],
        outputfile=str(params.output.scales_out)+'.png')
      if params.parameterisation.absorption_term:
        plot_absorption_surface(experiments[0],
          outputfile=str(params.output.absorption_out)+'.png')
    elif isinstance(experiments[0].scaling_model, Model.XscaleScalingModel):
      if params.parameterisation.decay_term:
        plot_2D_decay_correction(experiments[0], reflections[0])

  elif params.output.experiment_range:
    for j in params.output.experiment_range:
      experiment = experiments[j]
      reflection = reflections[j]
      if isinstance(experiment.scaling_model, Model.AimlessScalingModel):
        plot_smooth_scales(params, experiment, reflection,
          outputfile=str(params.output.scales_out)+'_'+str(j+1)+'.png')
        if params.parameterisation.absorption_term:
          plot_absorption_surface(experiment,
            outputfile=str(params.output.absorption_out)+'_'+str(j+1)+'.png')
  else:
    for j, (experiment, reflection) in enumerate(zip(experiments, reflections)):
      if isinstance(experiment.scaling_model, Model.AimlessScalingModel):
        plot_smooth_scales(params, experiment, reflection,
          outputfile=str(params.output.scales_out)+'_'+str(j+1)+'.png')
        if params.parameterisation.absorption_term:
          plot_absorption_surface(experiment,
            outputfile=str(params.output.absorption_out)+'_'+str(j+1)+'.png')

  print("\nFinished plotting graphs of scale factors. \n")



def plot_smooth_scales(params, experiments, reflections, outputfile=None):
  plt.figure(figsize=(14, 8))
  if params.parameterisation.scale_term:
    reflections['norm_rot_angle'] = (reflections['xyzobs.px.value'].parts()[2]
      * experiments.scaling_model.scale_normalisation_factor)
    rel_values = flex.double(np.arange(0, int(max(reflections['norm_rot_angle'])) + 1, 0.1))
    scale_SF = experiments.scaling_model.components['scale']
    scale_SF.update_reflection_data(normalised_values=rel_values)
    scale_SF.calculate_scales()
    plt.subplot(2, 1, 1)
    plt.title('Smooth scale factors')
    plt.plot(rel_values, scale_SF.inverse_scales)
    plt.ylabel('Scale term')
    plt.xlabel('Normalised rotation angle')

  if params.parameterisation.decay_term:
    reflections['norm_time_values'] = (reflections['xyzobs.px.value'].parts()[2]
      * experiments.scaling_model.decay_normalisation_factor)
    rel_values = np.arange(0, int(max(reflections['norm_time_values'])) + 1, 0.1)
    decay_SF = experiments.scaling_model.components['decay']
    decay_SF.update_reflection_data(normalised_values=rel_values,
      dvalues=flex.double([1.0]*len(rel_values)))
    decay_SF.calculate_scales()
    plt.subplot(2, 1, 2)
    plt.ylabel('Relative B factor (' + r'$\AA^{2}$'+')')
    plt.xlabel('Normalised time value')
    plt.plot(rel_values, np.log(decay_SF.inverse_scales)*2.0) #convert scales to B values
  #plt.tight_layout()
  if outputfile:
    plt.savefig(outputfile)
    print("Saving plot to %s" % outputfile)
  else:
    plt.savefig('smooth_scale_factors.png')
    print("Saving plot to smooth_scale_factors.png")


def plot_2D_decay_correction(experiment, reflections, outputfile=None):
  
  reflections = reflections.select(reflections['d'] > 0.0)
  configdict = experiment.scaling_model.configdict
  reflections['normalised_res_values'] = (((1.0 / (reflections['d']**2))
      - configdict['resmin']) / configdict['res_bin_width'])
  reflections['norm_time_values'] = ((reflections['xyzobs.px.value'].parts()[2]
      - configdict['zmin']) / configdict['time_bin_width'])
  
  ndbins = experiment.scaling_model.configdict['n_res_param']
  nzbins = experiment.scaling_model.configdict['n_time_param']
  '''create a grid of x and y points and use these to generate scale factors'''
  max_res = int(max(reflections['normalised_res_values'])) + 1
  max_time = int(max(reflections['norm_time_values'])) + 1

  rel_values_1 = np.arange(0, max_res+0.1, 0.1)
  rel_values_2 = np.arange(0, max_time+0.1, 0.1)
  (n1, n2) = (len(rel_values_1), len(rel_values_2))
  rel_values_1 = np.tile(rel_values_1, n2)
  rel_values_2 = np.repeat(rel_values_2, n1)
  
  decay_factor = experiment.scaling_model.components['decay']
  decay_factor.update_reflection_data(rel_values_1, rel_values_2)
  decay_factor.calculate_scales()

  scales = decay_factor.inverse_scales

  G_fin_2d = np.reshape(list(scales), (n2, n1)).T
  G_fin_2d = G_fin_2d[1:-1,1:-1]
  #data_man.g_decay.calculate_scales_and_derivatives()
  G_fin = list(scales)

  plt.figure(figsize=(11,6))
  gs = gridspec.GridSpec(1, 2)
  ax1 = plt.subplot(gs[0, 0])
  ax2 = plt.subplot(gs[0, 1])
  ax2.hist(G_fin, 40, log=False)
  ax2.set_xlabel('Inverse scale factor')
  ax2.set_ylabel('Occurences')

  resmax = (1.0 / (min(reflections['d'])**2))
  resmin = (1.0 / (max(reflections['d'])**2))

  #print "dmin is %s" % (min(data_man.reflection_table['d']))
  #print "dmax is %s" % (max(data_man.reflection_table['d']))
  #determine boundaries in res
  resbin_boundaries = np.arange(resmin, resmax, 2*(resmax - resmin)/(ndbins-1))
  #print resbin_boundaries
  dbin_boundaries = 1.0/(resbin_boundaries**0.5)
  #print dbin_boundaries
  dbin_boundaries = ['%.3f' % x for x in dbin_boundaries]

  im = ax1.imshow(G_fin_2d, cmap='viridis', origin='upper', aspect='auto')
  divider = make_axes_locatable(ax1)
  cax1 = divider.append_axes("right", size="5%", pad=0.05)
  cbar = plt.colorbar(im, cax=cax1)
  ax1.set_ylabel('d-value')
  ax1.set_xlabel('Normalised time value')
  ax1.set_yticks(np.arange(0, (max_res * 10)+0.01, 20))
  ax1.set_yticklabels(dbin_boundaries)
  ax1.set_xticks(np.arange(0, (max_time * 10)+0.01, 20))
  ax1.set_xticklabels(np.arange(0, max_time+0.01, 2))
  ax1.set_title('Inverse scale factors for decay correction', fontsize=12)
  plt.tight_layout()
  if outputfile:
    plt.savefig(outputfile)
  else:
    plt.savefig('g_decay.png')



def plot_absorption_surface(experiment, outputfile=None):
  params = experiment.scaling_model.components['absorption'].parameters

  from scitbx import math
  from scitbx.array_family import flex
  import math as pymath
  order = int(-1.0 + ((1.0 + len(params))**0.5))
  lfg =  math.log_factorial_generator(2 * order + 1)
  STEPS = 50
  phi = np.linspace(0, 2 * np.pi, 2*STEPS)
  theta = np.linspace(0, np.pi, STEPS)
  THETA, PHI = np.meshgrid(theta, phi)
  lmax = int(-1.0 + ((1.0 + len(params))**0.5))
  Intensity = np.ones(THETA.shape)
  counter = 0
  sqrt2 = pymath.sqrt(2)
  nsssphe = math.nss_spherical_harmonics(order, 5000, lfg)
  for l in range(1, lmax+1):
    for m in range(-l, l+1):
      for it, t in enumerate(theta):
        for ip, p in enumerate(phi):
          Ylm = nsssphe.spherical_harmonic(l, abs(m), t, p)
          if m < 0:
            r = sqrt2 * ((-1) ** m) * Ylm.imag
          elif m == 0:
            assert Ylm.imag == 0.0
            r = Ylm.real
          else:
            r = sqrt2 * ((-1) ** m) * Ylm.real
          Intensity[ip, it] += params[counter] * r
      counter += 1
  Intensity = 1.0/Intensity #make scale factor, not inverse

  if Intensity.max() - Intensity.min() != 0.0:
    rel_Int = (Intensity - Intensity.min())/(Intensity.max() - Intensity.min())
  else:
    rel_Int = Intensity
  #print "max, min absorption factors are (%s,%s)" % (Intensity.max(),Intensity.min())
  plt.figure(figsize=(8,6))
  gs = gridspec.GridSpec(1, 1)
  ax = plt.subplot(gs[0, 0])
  im = ax.imshow(rel_Int.T, cmap='viridis', origin='lower')
  ax.set_yticks([0,  (STEPS-1)/4.0, (STEPS-1)/2.0, 3.0*(STEPS-1)/4.0, STEPS-1])
  ax.set_yticklabels([0, 45, 90, 135, 180])
  ax.set_ylabel('Phi (degrees)')
  ax.set_xticks([0.0, (2.0*STEPS-1)/4.0, (2.0*STEPS-1)/2.0, 3.0*(2.0*STEPS-1)/4.0, (2.0*STEPS-1)])
  ax.set_xticklabels([0, 90, 180, 270, 360])
  ax.set_xlabel('Theta (degrees)')
  ax.set_title('Scale factors for absorption correction (note: not inverse scales)')
  divider = make_axes_locatable(ax)
  cax1 = divider.append_axes("right", size="5%", pad=0.05)
  cbar = plt.colorbar(im, cax=cax1,ticks=[0, 0.25, 0.5, 0.75, 1])
  cbar.ax.set_yticklabels(['%.6f' % Intensity.min(),
                           '%.6f' % ((Intensity.min()*0.75) + (Intensity.max()*0.25)),
                           '%.6f' % ((Intensity.min()*0.5) + (Intensity.max()*0.5)),
                           '%.6f' % ((Intensity.min()*0.25) + (Intensity.max()*0.75)),
                           '%.6f' % Intensity.max()])
  if outputfile:
    plt.savefig(outputfile)
    print("Saving plot to %s" % outputfile)
  else:
    plt.savefig('absorption_surface.png')
    print("Saving plot to absorption_surface.png")

if __name__ == "__main__":
  try:
    sys.exit(main(sys.argv[1:]))
  except Exception as e:
    halraiser(e)
