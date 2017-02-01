import dolfyn.adv.turbulence as turb
import numpy as np


def t_set(advr, n_bin, n_fft=None):
    # note, can get more accurate t_range by reducing the bin size

    # create a TurbBinner object
    calculator = turb.TurbBinner(n_bin, advr.fs, n_fft=n_fft)
    out = turb.VelBinnerSpec.__call__(calculator, advr)

    # perform the average and variance
    calculator.do_var(advr, out)
    calculator.do_avg(advr, out)

    # add the standard deviation
    out.add_data('sigma_Uh',
                 np.std(calculator.reshape(advr.U_mag), -1, dtype=np.float64) -
                 (advr.noise[0] + advr.noise[1]) / 2, 'main')

    # define just the u velocity variance
    u_var = out.vel_var[0]
    # u_vel = out.vel[0]

    timeset = []
    for i, j in zip(u_var, out.mpltime):
        if i < 1:
            timeset.append(j)

    start = timeset[0]
    end = timeset[len(timeset)-1]
    t_range = [start, end]

    return t_range
