/*
 * beam_vector_map.h
 *
 *  Copyright (C) 2013 Diamond Light Source
 *
 *  Author: James Parkhurst
 *
 *  This code is distributed under the BSD license, a copy of which is
 *  included in the root directory of this package.
 */
#ifndef DIALS_ALGORITHMS_REFLEXION_BASIS_BEAM_VECTOR_MAP_H
#define DIALS_ALGORITHMS_REFLEXION_BASIS_BEAM_VECTOR_MAP_H

#include <scitbx/vec2.h>
#include <scitbx/vec3.h>
#include <scitbx/array_family/flex_types.h>
#include <dxtbx/model/beam.h>
#include <dxtbx/model/detector.h>

namespace dials { namespace algorithms { namespace reflexion_basis {
    namespace transform {

  using scitbx::vec2;
  using scitbx::vec3;
  using scitbx::af::flex_grid;
  using dxtbx::model::Beam;
  using dxtbx::model::Detector;

  typedef scitbx::af::flex< vec3<double> >::type flex_vec3_double;

  /**
   * Calculate the beam vector at every pixel on the detector, sub-divided
   * into (n_div * n_div) equal areas. This is done to remove a certain
   * amount of processing from being done per reflection and ensuring it
   * is only done before the reflections are procesed.
   * @param detector The detector model
   * @param beam The beam model
   * @param n_div The number of sub-divisions to use
   * @param corner Calculate coordinates at corners or centre
   * @returns An array of beam vectors
   */
  inline
  flex_vec3_double beam_vector_map(const Detector &detector, const Beam &beam,
      std::size_t n_div, bool corner)
  {
    // check the input
    DIALS_ASSERT(beam.get_wavelength() > 0.0);
    DIALS_ASSERT(n_div > 0);

    // Calculate the image size
    vec2<std::size_t> image_size = detector.get_image_size();
    std::size_t x_size = image_size[0] * n_div;
    std::size_t y_size = image_size[1] * n_div;
    if (corner) {
      x_size += 1;
      y_size += 1;
    }

    // Scale factors
    double n_div_r = 1.0 / (double)n_div;
    double wavelength_r = 1.0 / beam.get_wavelength();

    // Create the necessary arrays
    flex_vec3_double detector_s1(flex_grid<>(y_size, x_size));

    // Add an offset if not corners
    double offset = 0.0;
    if (corner == false) {
      offset = 0.5;
    }

    // Calculate the beam vectors for each sub-division of the detector
    for (std::size_t j = 0, k = 0; j < y_size; ++j) {
      for (std::size_t i = 0; i < x_size; ++i, ++k) {
        double x = (i + offset) * n_div_r;
        double y = (j + offset) * n_div_r;
        vec2<double> px(x, y);
        detector_s1[k] = detector.get_pixel_lab_coord(
          px).normalize() * wavelength_r;
      }
    }

    // Return the s1 vector
    return detector_s1;
  }

  /**
   * Calculate the beam vector at every pixel on the detector.
   * @param detector The detector model
   * @param beam The beam model
   * @param corner Calculate coordinates at corners or centre
   * @returns An array of beam vectors
   */
  inline
  flex_vec3_double beam_vector_map(const Detector &detector,
      const Beam &beam, bool corner)
  {
    return beam_vector_map(detector, beam, 1, corner);
  }

  /**
   * Calculate the beam vector at every pixel on the detector.
   * @param detector The detector model
   * @param beam The beam model
   * @returns An array of beam vectors
   */
  inline
  flex_vec3_double beam_vector_map(const Detector &detector,
      const Beam &beam)
  {
    return beam_vector_map(detector, beam, 1, false);
  }

}}}} // namespace dials::algorithms::reflexion_basis::transform

#endif /* DIALS_ALGORITHMS_REFLEXION_BASIS_BEAM_VECTOR_MAP_H */
