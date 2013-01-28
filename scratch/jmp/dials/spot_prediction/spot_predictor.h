
#ifndef DIALS_SPOT_PREDICTION_SPOT_PREDICTOR_H
#define DIALS_SPOT_PREDICTION_SPOT_PREDICTOR_H

#include <scitbx/constants.h>
#include "../equipment/beam.h"
#include "../equipment/detector.h"
#include "../equipment/goniometer.h"
#include "index_generator.h"
#include "xds_rotation_angles.h"
#include "../geometry/transform/from_beam_vector_to_detector.h"


namespace dials { namespace spot_prediction {

class SpotPredictor {

public:
    
    /** 
     * Initialise the spot predictor.
     * @param beam The beam parameters
     * @param detector The detector parameters
     * @param gonio The goniometer parameters
     * @param unit_cell The unit cell parameters
     * @param space_group_type The space group struct
     * @param ub_matrix The ub matrix
     * @param d_min The resolution
     */
    SpotPredictor(const equipment::Beam &beam,
                  const equipment::Detector &detector,
                  const equipment::Goniometer &gonio,
                  const cctbx::uctbx::unit_cell &unit_cell,
                  const cctbx::sgtbx::space_group_type &space_group_type,
                  scitbx::mat3 <double> ub_matrix,
                  double d_min)
        : index_generator_(unit_cell, space_group_type, false, d_min),
          rotation_angle_calculator_(
            beam.get_direction().normalize() / beam.get_wavelength(), 
            gonio.get_rotation_axis()),
          from_beam_vector_to_detector_(detector),
          beam_(beam),
          detector_(detector),
          gonio_(gonio),
          ub_matrix_(ub_matrix) {}

    /**
     * Predict the spot locations on the image detector.
     *  
     * The algorithm performs the following procedure:
     *   
     *  - First the set of miller indices are generated.
     *    
     *  - For each miller index, the rotation angle at which the diffraction
     *    conditions are met is calculated.
     *      
     *  - The rotation angles are then checked to see if they are within the
     *    rotation range.
     *      
     *  - The reciprocal lattice vectors are then calculated, followed by the
     *    diffracted beam vector for each reflection.
     *      
     *  - The image volume coordinates are then calculated for each reflection.
     *      
     *  - The image volume coordinates are then checked to see if they are
     *    within the image volume itself.
     */
    void predict() {

        // Reset all the arrays
        miller_indices_.clear();
        rotation_angles_.clear();
        beam_vectors_.clear();
        image_coords_.clear();

        // Get the beam direction and rotation axis
        scitbx::vec3 <double> s0(beam_.get_direction().normalize() / 
                                 beam_.get_wavelength());
        scitbx::vec3 <double> m2(gonio_.get_rotation_axis().normalize());

        // Continue looping until we run out of miller indices        
        for (;;) {
            
            // Get the next miller index
            cctbx::miller::index <> h = index_generator_.next();
            if (h.is_zero()) {
                break;
            }

            // Calculate the reciprocal space vector
            scitbx::vec3 <double> pstar0 = ub_matrix_ * h;

            // Try to calculate the diffracting rotation angles
            scitbx::vec2 <double> phi;
            try {
                phi = rotation_angle_calculator_.calculate(pstar0);
            } catch(error) {
                continue;
            }

            // Loop through the 2 rotation angles
            for (std::size_t i = 0; i < phi.size(); ++i) {

                // Check that the angles are within the rotation range
                double phi_deg = scitbx::rad_as_deg(phi[i]);
                if (!gonio_.is_angle_valid(phi_deg)) {
                    continue;
                }

                // Calculate the reciprocal space vector
                scitbx::vec3 <double> pstar = pstar0.unit_rotate_around_origin(
                                                    m2, phi[i]);
                
                // Calculate the diffracted beam vector
                scitbx::vec3 <double> s1 = s0 + pstar;
                 
                // Try to calculate the detector coordinate              
                scitbx::vec2 <double> xy;
                try {
                    xy = from_beam_vector_to_detector_.apply(s1);
                } catch(error) {
                    continue;
                }
                
                // Calculate the frame number
                double z = gonio_.get_zero_based_frame_from_angle(phi_deg);
                
                // Check the detector coordinate is valid and add the 
                // elements to the arrays. NB. up to now, we have used 
                // angles in radians, convert them to degrees before adding
                // them to the rotation angle array.
                if (!detector_.is_coordinate_valid(xy)) {
                    continue;
                }
                miller_indices_.push_back(h);
                rotation_angles_.push_back(phi_deg);
                beam_vectors_.push_back(s1);
                image_coords_.push_back(scitbx::vec3 <double> (xy[0], xy[1], z));
            }
        }        
    }
    
    /** Get the array of miller indices */
    scitbx::af::shared <cctbx::miller::index <> > get_miller_indices() {
        return miller_indices_;
    }
    
    /** Get the rotation angles */
    scitbx::af::shared <double> get_rotation_angles() {
        return rotation_angles_;
    }
    
    /** Get the beam vectors */
    scitbx::af::shared <scitbx::vec3 <double> > get_beam_vectors() {
        return beam_vectors_;
    }
    
    /** Get the image coordinates */
    scitbx::af::shared <scitbx::vec3 <double> > get_image_coordinates() {
        return image_coords_;
    }
   
private:

    IndexGenerator index_generator_;
    XdsRotationAngles rotation_angle_calculator_;
    geometry::transform::FromBeamVectorToDetector from_beam_vector_to_detector_;
    equipment::Beam beam_;
    equipment::Detector detector_;
    equipment::Goniometer gonio_;
    scitbx::mat3 <double> ub_matrix_;
    scitbx::af::shared <cctbx::miller::index <> > miller_indices_;
    scitbx::af::shared <double> rotation_angles_;
    scitbx::af::shared <scitbx::vec3 <double> > beam_vectors_;
    scitbx::af::shared <scitbx::vec3 <double> > image_coords_;    
};

}} // namespace dials::spot_prediction

#endif // DIALS_SPOT_PREDICTION_SPOT_PREDICTOR_H
