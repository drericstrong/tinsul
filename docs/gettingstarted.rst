====================
 2. Getting Started
====================

Installation
--------------
TInsul can be installed using pip:

**pip install tinsul**

**Other required libraries**: numba, numpy, pandas

Examples
-------------
The main function within TInsul is called "tinsul_sim". It requires only two inputs, although a number of other optional inputs can also be supplied. "temps" is a 12x3 matrix, with the rows being months of the year (starting with January), and the columns being the low, average, and high temperatures per month, respectively. "start_month" refers to the month at which to begin the simulation, with 1 being January, 2 being February, etc.

For example:

>>> temps = [[-2, 1, 6], [-1, 3, 8], [3, 7, 13], [8, 13, 19], [14, 18, 24], [19, 24, 29], [22, 28, 31], [21, 27, 30], [17, 22, 26], [10, 15, 20], [5, 10, 14], [0, 4, 8]]

>>> start_month = 1

>>> co, co2 = tinsul_sim(temps, start_month)

The output of the tinsul_sim function will be a tuple containing the carbon monoxide and carbon dioxide accumulation per week (co, co2 above). The size of the array can be used to infer the failure time, in weeks.
