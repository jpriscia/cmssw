#ifndef TrackReco_HelixParameters_h
#define TrackReco_HelixParameters_h
/** \class reco::helix::Parameters
 *  
 * Model of 5 helix parameters for Track fit 
 * according to how described in the following document:
 *
 *   http://www-jlc.kek.jp/subg/offl/lib/docs/helix_manip/main.html
 *
 * The class Covariance is a model of 5x5 covariance matrix 
 * for helix parameters
 * 
 * \author Luca Lista, INFN
 *
 * \version $Id: HelixParameters.h,v 1.6 2006/03/01 12:28:44 llista Exp $
 *
 */

#include "DataFormats/Math/interface/Vector3D.h"
#include "DataFormats/Math/interface/Point3D.h"
#include "DataFormats/Math/interface/Error.h"
#include "DataFormats/Math/interface/Vector.h"
#include <cmath>

namespace reco {
  namespace helix {
    /// enumerator provided indices to the five parameters
    enum index { i_d0 = 0, i_phi0, i_omega, i_dz, i_tanDip }; 
    /// position-momentum covariance matrix (6x6).
    /// This type will be replaced by a MathCore symmetric
    /// matrix, as soon as available
    typedef math::Error<6> PosMomError;
    /// spatial vector
    typedef math::XYZVector Vector;
    /// point in the space
    typedef math::XYZPoint Point;
    /// parameter vector.
    /// This type has to be replaced by MathCore type
    /// SVector<5, Double32_t>
    typedef math::Vector<5>::type ParameterVector;
    /// helix parameter covariance matrix (5x5)
    /// This type will be replaced by a MathCore symmetric
    /// matrix, as soon as available
    typedef math::Error<5> ParameterError;
 
    class Parameters {
    public:
      /// default constructor
      Parameters() { }
      /// constructor from five double parameters
      Parameters( double p1, double p2, double p3, double p4, double p5 ) : 
	par_( p1, p2, p3, p4, p5 ) { }
      /// index type
      typedef unsigned int index;
      /// accessing i-th parameter, i = 0, ..., 4 (read-only mode)
      double operator()( index i ) const { return par_( i ); }
      /// accessing i-th parameter, i = 0, ..., 4
      double & operator()( index i ) { return par_( i ); }
      /// track impact parameter (distance of closest approach to beamline) (read-only mode)
      double d0() const { return par_[ i_d0 ]; }
      /// track azimuthal angle of point of closest approach to beamline (read-only mode)
      double phi0() const { return par_[ i_phi0 ]; }
      /// e / pt (electric charge divided by transverse momentum) (read-only mode)     
      double omega() const { return par_[ i_omega ]; }
      /// z coordniate of point of closest approach to beamline (read-only mode)
      double dz() const { return par_[ i_dz ]; }
      /// tangent of the dip angle ( tanDip = pz / pt ) (read-only mode)
      double tanDip() const { return par_[ i_tanDip ]; }
      /// track impact parameter (distance of closest approach to beamline)
      double & d0() { return par_[ i_d0 ]; }
      /// track azimuthal angle of point of closest approach to beamline
      double & phi0() { return par_[ i_phi0 ]; }
      /// e / pt (electric charge divided by transverse momentum)      
      double & omega() { return par_[ i_omega ]; }
      /// z coordniate of point of closest approach to beamline
      double & dz() { return par_[ i_dz ]; }
      /// tangent of the dip angle ( tanDip = pz / pt )
      double & tanDip() { return par_[ i_tanDip ]; }
      /// electric charge
      int charge() const;
      /// transverse momentum
      double pt() const;
      /// momentum vector
      Vector momentum() const;
      /// position of point of closest approach to the beamline
      Point vertex() const;
      
    private:
      /// five parameters
      ParameterVector par_;
    };
  
    class Covariance {
    public:
      /// default constructor
      Covariance() {} 
      /// constructor from double * (15 parameters)
      Covariance( const double * cov ) : cov_( cov ) { }
      /// index type
      typedef unsigned int index;
      /// accessing (i, j)-th parameter, i, j = 0, ..., 4 (read only mode)
      double operator()( index i, index j ) const { return cov_( i, j ); }
      /// accessing (i, j)-th parameter, i, j = 0, ..., 4
      double & operator()( index i, index j ) { return cov_ ( i, j ); }
      /// error on d0
      double d0Error() const { return sqrt( cov_.get<i_d0, i_d0>() ); }
      /// error on phi0
      double phi0Error() const { return sqrt( cov_.get<i_phi0, i_phi0>() ); }
      /// error on omega
      double omegaError() const { return sqrt( cov_.get<i_omega, i_omega>() ); }
      /// error on dx
      double dzError() const { return sqrt( cov_.get<i_dz, i_dz>() ); }
      /// error on tanDip
      double tanDipError() const { return sqrt( cov_.get<i_tanDip, i_tanDip>() ); }

    private:
      /// 5x5 matrix
      ParameterError cov_;
    };
    
    /// convert from cartesian coordinates to 5-helix parameters.
    /// The point passed must be the point of closest approach to the beamline
    void setFromCartesian( int q, const Point &, const Vector &, 
			   const PosMomError & ,
			   Parameters &, Covariance & ); 

    /// compute position-momentum 6x6 degenerate covariance matrix
    /// from 5 parameters and 5x5 covariance matrix
    PosMomError posMomError( const Parameters &, const Covariance & );

    inline int Parameters::charge() const {
      return omega() > 0 ? +1 : -1;
    }
    
    inline double Parameters::pt() const {
      return 1./ fabs( omega() );
    }
    
    inline Vector Parameters::momentum() const {
      double p_t = pt();
      return Vector( - p_t * sin( phi0() ), p_t * cos( phi0() ), p_t * tanDip() );
    }
    
    inline Point Parameters::vertex() const {
      return Point( d0() * cos( phi0() ), d0() * sin( phi0() ), dz() );
    }

  }
}


#endif
