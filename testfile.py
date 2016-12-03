import dolfyn.adp.api as apm

# Only read the first 500 pings
nens = 500

# Or read all of the pings
# nens = None

dat = apm.read_rdi('SMADCP-FEM-Brehat-1.000', nens)
