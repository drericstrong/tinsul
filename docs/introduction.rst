=====================
 1. Introduction
=====================
TInsul (Transformer INSULation simulator) is a Python module to simulate condition-monitoring data for the paper insulation of large-scale transformers. It might be used to test new prognostics algorithms, as a teaching aid for those new to the field of condition-monitoring, or to compare the results from simulated data to real-world applications.

TInsul requires the following primary inputs:

* Average temperatures per month
* Starting month (optional)
* Overload ratio (optional)

and will provide these output values (per week):

* CO generation
* CO2 generation
* Furan
* Furfural
* Water Content
* Failure time (inferred from the size of the array)

*Several simplifying assumptions were made when developing TInsul, and empirical data from an academic paper was used to estimate the rate of dissolved gas accumulation per week. While the simulated data from TInsul will be relatively realistic, its real-world applicability should be treated with some caution.* 