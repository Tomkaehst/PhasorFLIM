# Functions approximating pulsed laser sources in two modes: Gaussian and modulated

laser.gauss = function(x, amp = 0.01, dplace = 2500, grsm = 100) {
  y = amp * exp(-(x - dplace)^2/(2*grsm^2))
}


laser.modulated = function(x, amp = 0.5, verticalDplace = 0, peri = 0.5) y = amp * sin(per*x + dplace) + amp 



laser.afterbump = function(x, amp1, dplace1, grsm1, amp2, dplace2, grsm2) {
  y = amp1 * exp(-(x - dplace1)^2/(2*grsm1^2)) + amp2 * exp(-(x - dplace2)^2/(2*grsm2^2))
}


# laser.afterbump() only fits the little ripple in front of the IRF. I add another Gaussian curve term to fit the actucal afterbump several hundred ps after the first, large peak
laser.afterbump2 = function(t, a1, a2, a3, d1, d2, d3, g1, g2, g3) {
  a1*exp(-(t-d1)^2/(2*g1)^2) + a2*exp(-(t-d2)^2/(2*g2)^2) + a3*exp(-(t-d3)^2/(2*g3)^2)
}

