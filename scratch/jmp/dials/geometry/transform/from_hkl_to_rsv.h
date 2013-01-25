#ifndef DIALS_GEOMETRY_TRANSFORM_FROM_HKL_TO_RSV_H
#define DIALS_GEOMETRY_TRANSFORM_FROM_HKL_TO_RSV_H

#include <scitbx/vec3.h>
#include <scitbx/mat3.h>
#include <scitbx/array_family/flex_types.h>
#include <scitbx/constants.h>
#include <cctbx/miller.h>
#include "../../error.h"

namespace dials { namespace geometry { namespace transform {

typedef cctbx::miller::index <> miller_index;
typedef scitbx::af::flex <scitbx::vec3 <double> >::type flex_vec3_double;
typedef scitbx::af::flex <miller_index>::type flex_miller_index;

class FromHklToRsv {

public:

    /** Default constructor */
    FromHklToRsv() {}

    FromHklToRsv(scitbx::mat3 <double> ub, scitbx::vec3 <double> m2) 
        : ub_(ub),
          m2_(m2.normalize()) {}

    scitbx::vec3 <double> apply(miller_index h, double phi) {
        return (ub_ * h).unit_rotate_around_origin(
            m2_, scitbx::deg_as_rad(phi));
    }

    flex_vec3_double apply(const flex_miller_index &h, 
                           const scitbx::af::flex_double &phi) {
        DIALS_ASSERT(h.size() == phi.size());
        flex_vec3_double result(h.size());
        for (int i = 0; i < h.size(); ++i) {
            result[i] = apply(h[i], phi[i]);
        }
        return result;
    }

private:

    scitbx::mat3 <double> ub_;
    scitbx::vec3 <double> m2_;
};

}}} // namespace dials::geometry::transform

#endif // DIALS_GEOMETRY_TRANSFORM_FROM_HKL_TO_RSV_H
