# -*- coding: utf-8 -*-
# Copyright 2016-2020 The pyXem developers
#
# This file is part of pyXem.
#
# pyXem is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyXem is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyXem.  If not, see <http://www.gnu.org/licenses/>.

"""Variance generators in real and reciprocal space for fluctuation electron microscopy."""

import numpy as np
from hyperspy.signals import Signal2D
from hyperspy.api import stack

from pyxem.signals import DiffractionVariance2D, ImageVariance
from pyxem.utils.signal import (
    transfer_navigation_axes_to_signal_axes,
    transfer_signal_axes,
)


class VarianceGenerator:
    """Generates variance images for a specified signal and set of aperture
    positions.

    Parameters
    ----------
    signal : ElectronDiffraction2D
        The signal of electron diffraction patterns to be indexed.

    """

    def __init__(self, signal, *args, **kwargs):
        self.signal = signal
        self.thickness_filter = None


        # add a check for calibration

    def get_image_variance(self, dqe):
        """Calculates the variance in scattered intensity as a function of
        scattering vector. The calculated variance is normalised by the mean
        squared, as is appropriate for the distribution of intensities. This
        causes a problem if Poisson noise is significant in the data, resulting
        in a divergence of the Poisson noise term. To in turn remove this
        effect, we subtract a dqe/mean_dp term (although it is suggested that
        dqe=1) from the data, creating a "poisson noise-free" corrected variance
        pattern. DQE is fitted to make this pattern flat.

        Parameters
        ----------
        dqe : float
            Detective quantum efficiency of the detector for Poisson noise
            correction.

        Returns
        -------
        varims : ImageVariance
            A two dimensional Signal class object containing the mean DP, mean
            squared DP, and variance DP, and a Poisson noise-corrected variance
            DP.
        """
        im = self.signal.T
        mean_im = im.mean((0, 1))
        meansq_im = Signal2D(np.square(im.data)).mean((0, 1))
        normvar = (meansq_im.data / np.square(mean_im.data)) - 1.0
        var_im = Signal2D(normvar)
        corr_var_array = normvar - (np.divide(dqe, mean_im.data))
        corr_var_array[np.invert(np.isfinite(corr_var_array))] = 0
        corr_var = Signal2D(corr_var_array)
        varims = stack((mean_im, meansq_im, var_im, corr_var))

        sig_x = varims.data.shape[1]
        sig_y = varims.data.shape[2]
        iv = ImageVariance(varims.data.reshape((2, 2, sig_x, sig_y)))
        iv = transfer_navigation_axes_to_signal_axes(iv, self.signal)

        return iv
