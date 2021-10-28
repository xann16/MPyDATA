""" antidiffusive velocity formulae incl. divergent-flow,
    third-order-terms, DPDC and partially also infinite-gauge logic """
import numba
import numpy as np
from PyMPDATA.impl.enumerations import MAX_DIM_NUM


def make_antidiff(non_unit_g_factor, options, traversals, last_pass=False):
    if options.n_iters <= 1:
        @numba.njit(**options.jit_flags)
        # pylint: disable=too-many-arguments
        def apply(_1, _2, _3, _4, _5, _6, _7):
            return
    else:
        idx = traversals.indexers[traversals.n_dims]
        apply_vector = traversals.apply_vector()

        formulae_antidiff = tuple(
            __make_antidiff(idx.atv[i], idx.ats[i],
                            non_unit_g_factor=non_unit_g_factor,
                            options=options,
                            n_dims=traversals.n_dims,
                            last_pass=last_pass)
            if idx.ats[i] is not None else None
            for i in range(MAX_DIM_NUM))

        @numba.njit(**options.jit_flags)
        # pylint: disable=too-many-arguments
        def apply(GC_corr, psi, psi_bc, GC_unco, vec_bc, g_factor, g_factor_bc):
            return apply_vector(*formulae_antidiff, *GC_corr, *psi, *psi_bc, *GC_unco, *vec_bc,
                                *g_factor, *g_factor_bc)

    return apply


def __make_antidiff(atv, ats, non_unit_g_factor, options, n_dims, last_pass):
    infinite_gauge = options.infinite_gauge
    divergent_flow = options.divergent_flow
    third_order_terms = options.third_order_terms
    epsilon = options.epsilon
    DPDC = options.DPDC
    dimensionally_split = options.dimensionally_split

    @numba.njit(**options.jit_flags)
    def A(psi):
        """ eq. 13 in Smolarkiewicz 1984; eq. 17a in Smolarkiewicz & Margolin 1998 """
        result = ats(*psi, 1) - ats(*psi, 0)
        if infinite_gauge:
            return result / 2
        return result / (ats(*psi, 1) + ats(*psi, 0) + epsilon)

    @numba.njit(**options.jit_flags)
    def B(psi):
        """ eq. 13 in Smolarkiewicz 1984; eq. 17b in Smolarkiewicz & Margolin 1998 """
        result = (
            ats(*psi, 1, 1) + ats(*psi, 0, 1) -
            ats(*psi, 1, -1) - ats(*psi, 0, -1)
        )
        if infinite_gauge:
            return result / 4

        return result / (
            ats(*psi, 1, 1) + ats(*psi, 0, 1) +
            ats(*psi, 1, -1) + ats(*psi, 0, -1) +
            epsilon
        )

    @numba.njit(**options.jit_flags)
    def antidiff_basic(psi, GC, _):
        """ eq. 13 in Smolarkiewicz 1984 """
        tmp = A(psi)
        result = (np.abs(atv(*GC, .5)) - atv(*GC, +.5) ** 2) * tmp
        if DPDC and last_pass:
            a = (1 / (1 - np.abs(tmp)))
            b = - (tmp*a)/(1 - tmp**2)
            result = result * (result * b + a)
        if n_dims == 1 or dimensionally_split:
            return result
        return result - (
            0.5 * atv(*GC, .5) *
            0.25 * (atv(*GC, 1., +.5) + atv(*GC, 0., +.5) + atv(*GC, 1., -.5) + atv(*GC, 0., -.5)) *
            B(psi)
        )

    @numba.njit(**options.jit_flags)
    def antidiff_variants(psi, GC, G):
        """ eq. 13 in Smolarkiewicz 1984 """
        result = antidiff_basic(psi, GC, G)

        G_bar = (ats(*G, 1) + ats(*G, 0)) / 2 if non_unit_g_factor else 1

        # third-order terms
        if third_order_terms:
            # assert psi.dimension < 3  # TODO #96
            tmp = (
                3 * atv(*GC, .5) * np.abs(atv(*GC, .5)) / G_bar
                -2 * atv(*GC, .5) ** 3 / G_bar ** 2
                -atv(*GC, .5)
            ) / 6

            tmp *= 2 * (ats(*psi, 2) - ats(*psi, 1) - ats(*psi, 0) + ats(*psi, -1))

            if infinite_gauge:
                tmp /= (1 + 1 + 1 + 1)
            else:
                tmp /= ats(*psi, 2) + ats(*psi, 1) + ats(*psi, 0) + ats(*psi, -1) + epsilon

            result += tmp

            if n_dims > 1:
                GC1_bar = (
                    atv(*GC, 1, .5) +
                    atv(*GC, 0, .5) +
                    atv(*GC, 1, -.5) +
                    atv(*GC, 0, -.5)
                ) / 4
                tmp = GC1_bar / (2 * G_bar) * (
                    np.abs(atv(*GC, .5)) - 2 * atv(*GC, .5) ** 2 / G_bar
                )

                tmp *= 2 * (ats(*psi, 1, 1) - ats(*psi, 0, 1) - ats(*psi, 1, -1) + ats(*psi, 0, -1))

                if infinite_gauge:
                    tmp /= (1 + 1 + 1 + 1)
                else:
                    tmp /= (ats(*psi, 1, 1) + ats(*psi, 0, 1) + ats(*psi, 1, -1) + ats(*psi, 0, -1))

                result += tmp

        # divergent flow option
        # eq.(30) in Smolarkiewicz_and_Margolin_1998
        if divergent_flow:
            # assert psi.dimension == 1
            tmp = -.25 * atv(*GC, .5) * (atv(*GC, 1.5) - atv(*GC, -.5))
            if non_unit_g_factor:
                tmp /= G_bar
            if infinite_gauge:
                tmp *= .5 * ats(*psi, 1) + ats(*psi, 0)

            result += tmp
        return result
    return antidiff_variants if divergent_flow or third_order_terms else antidiff_basic
