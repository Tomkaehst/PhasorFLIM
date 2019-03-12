/* file monoDecay.c */

#include <R.h>

static double parms[3];

#define k1 parms[0]
#define k2 parms[1]
#define k3 parms[2]

void initmod(void (* odeparms)(int *, double *)) {
  int N=3;
  odeparms(&N, parms);
}

void derivs (int *neq, double *t, double *y, double *ydot,
             double *yout, int *ip) {
  if (ip[0] <1) error("nout should be at least 1");
  
 // double temp = exp((t[0] - 2000.0)/(200^2));
  //ydot[2] = 100 * exp(k2);
  ydot[0] = -(1/k1)*y[0];
  ydot[1] = (1/k1)*y[0] - (1/k2)*y[1];
  ydot[2] = (1/k2)*y[1] - (1/k3)*y[2];
  
  
  yout[0] = y[0]+y[1] + y[2];
}

/* END file monoDecay.c */