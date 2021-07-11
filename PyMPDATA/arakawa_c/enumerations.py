import numpy as np

ARG_FOCUS, ARG_DATA, ARG_DATA_OUTER, ARG_DATA_MID3D, ARG_DATA_INNER = 0, 1, 1, 2, 3

MAX_DIM_NUM = 3

OUTER, MID3D, INNER = 0, 1, -1

IMPL_META_AND_DATA = 0
IMPL_BC = 1

META_AND_DATA_META = 0

SIGN_LEFT, SIGN_RIGHT = +1, -1

RNG_START, RNG_STOP, RNG_STEP = 0, 1, 2

INVALID_INDEX = -44

INVALID_INIT_VALUE = np.nan

INVALID_HALO_VALUE = 666

INVALID_NULL_VALUE = 0

ONE_FOR_STAGGERED_GRID = 1
