/* file monoDecay.c */

#include <R.h>

static double parms[3];

#define tau1 parms[0]
#define tau2 parms[1]
#define FRET parms[2]

void initmod(void (* odeparms)(int *, double *)) {
  int N=4;
  odeparms(&N, parms);
}

void derivs (int *neq, double *t, double *y, double *ydot,
             double *yout, int *ip) {
  if (ip[0] <1) error("nout should be at least 1");

  ydot[0] = -(1/tau1)*y[0];
  ydot[1] = -ydot[0];
  ydot[2] = (1/FRET)*y[0] - (1/tau2)*y[2];
  ydot[3] = -ydot[2];
  
  
  yout[0] = y[0]+ y[1] + y[2] + y[3];
}

/* END file monoDecay.c */