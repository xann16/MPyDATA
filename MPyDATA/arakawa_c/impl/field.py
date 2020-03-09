import numba
from MPyDATA.clock import time


class Field:
    class Impl:
        dimension: int
        halo: int
        axis: int

        def at(self, i: [int, float], j: [int, float] = -1, k: [int,float] = -1):
            raise NotImplementedError()

        def focus(self, i: int, j: int = -1, k: int = -1):
            raise NotImplementedError()

        def set_axis(self, d: int):
            raise NotImplementedError()

    _impl = None
    _halo_valid: bool = False

    def __init__(self, halo):
        self._halo = halo

    @property
    def halo(self):
        return self._halo

    @property
    def dimension(self):
        return self._impl.dimension

    def apply(self, args, ext=0):
        assert ext < self.halo

        # t0 = time()

        for arg in args:
            arg.fill_halos()

        if len(args) == 1:
            self._impl.apply_1arg(args[0]._impl, ext)
        elif len(args) == 2:
            self._impl.apply_2arg(args[0]._impl, args[1]._impl, ext)
        else:
            raise NotImplementedError()

        self._halo_valid = False
        # print(time()-t0, "     apply()", body.py_func.__name__)

    def swap_memory(self, other):
        self._impl, other._impl = other._impl, self._impl
        self._halo_valid, other._halo_valid = other._halo_valid, self._halo_valid

    def _fill_halos_impl(self):
        raise NotImplementedError()

    def fill_halos(self):
        if self._halo_valid or self.halo == 0:
            return
        self._fill_halos_impl()
        self._halo_valid = True
