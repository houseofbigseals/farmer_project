
import logging


class SearchPoint(object):
    """
    Simple object that contains useful fields
    """
    def __init__(
            self,
            x1: float,
            x2: float,
            result: float,
            name: str
    ):
        self.x1 = x1
        self.x2 = x2
        self.result = result
        self.name = name


class StupidGradientMethod(object):
    """
    This object contains abstraction of dynamical search
    algorithm like gradient or newton or triangles
    it works with abstract values of functional F and coordinates
    It provides ability to calculate numerical value of
    derivative in finite difference form and other things like that
    """
    def __init__(
            self,
            start_x1: float,
            start_x2: float,
            h1: float = 20,
            h2: float = 0.1,
            lamb: float = 0.1,
            max_x1: float = 700,
            max_x2: float = 1.5,
            min_x1: float = 200,
            min_x2: float = 0
    ):
        # suppose we need to contain three values to calculate dF/dx
        # F(x1i, x2i), F(x1i + h, x2i), F(x1i, x2i + h)
        # x1 is summ FAR intensity and is about 200-700
        # x2 is intensity of red lite to intensity of white lite and is about 0-1.5 (0-3?)
        # F is quality coefficient for moon base Q taken with a minus sign
        # because we want to find maximum of Q
        # but gradient search finds only minimum
        # Q = ((0.28 * dCO2 + 0.72 * (dCO2/E))/current_mean_weight)
        # F = -Q, but we dont control it anywhere
        # logger
        self.logger = logging.getLogger("Worker.SearchMethods.StupidGradientMethod")
        # search constant parameters
        self.lamb = lamb
        # start points
        self.x1 = start_x1
        self.x2 = start_x2
        # steps by axis x1 and x2
        self.h1 = h1
        self.h2 = h2
        # points for calculating derivative in finite difference form
        self.dF = SearchPoint(self.x1, self.x2, 0, 'dF')
        self.dFx1 = SearchPoint(self.x1 + self.h1, self.x2, 0, 'dFx1')
        self.dFx2 = SearchPoint(self.x1, self.x2 + self.h2, 0, 'dFx2')
        # search area borders
        self.max_x1 = max_x1
        self.max_x2 = max_x2
        self.min_x1 = min_x1
        self.min_x2 = min_x2
        # current search table to expose it for search system
        # it contains [x1, x2, result, name_of_this_point]
        # search system should go through this list and put here
        # measured values of F = -Q instead zeros
        self.search_table = [
            self.dF,
            self.dFx1,
            self.dFx2
        ]
        self.logger.info("Method started")

    def do_search_step(self):
        """
        we should run this function only after setting all dF fields
        it must return new coordinates for that search step
        and update self x1, x2 and search table
        :return:

        """
        # suppose we need to contain three values to calculate dF/dx
        # F(x1i, x2i), F(x1i + h1, x2i), F(x1i, x2i + h2) and x1i, x2i
        # save old x1 and x2
        x1_old = self.x1
        x2_old = self.x2
        # lets check if dF.results is not zero
        for p in self.search_table:
            if p.result == 0:
                raise ValueError("Value of {} was not measured".format(p.name))
        # if all is ok lets calculate new x1 and x2
        x1_new = self.x1 - self.lamb * ((self.dFx1.result - self.dF.result) / self.h1)
        x2_new = self.x2 - self.lamb * ((self.dFx2.result - self.dF.result) / self.h2)
        # then lets do some security checks
        # for example, lets check if we are outside the range of acceptable values
        if x1_new < self.min_x1:
            # lets set x1 as lower acceptable limit
            x1_new = self.min_x1
        elif x1_new > self.max_x1:
            # lets set x1 as higher acceptable limit
            x1_new = self.max_x1

        if x2_new < self.min_x2:
            # lets set x2 as lower acceptable limit
            x2_new = self.min_x2
        elif x2_new > self.max_x2:
            # lets set x2 as higher acceptable limit
            x2_new = self.max_x2

        # then set them as new current coordinates
        self.x1 = x1_new
        self.x2 = x2_new
        # recalculate all dF things
        self.dF = SearchPoint(self.x1, self.x2, 0, 'dF')
        self.dFx1 = SearchPoint(self.x1 + self.h1, self.x2, 0, 'dFx1')
        self.dFx2 = SearchPoint(self.x1, self.x2 + self.h2, 0, 'dFx2')
        # recalculate search table
        self.search_table = [
            self.dF,
            self.dFx1,
            self.dFx2
        ]
        self.logger.info("done search step from x1 = {} x2 = {} to x1 = {} x2 = {}".format(
            x1_old, x2_old, x1_new, x2_new
        ))
        # return new x1 and x2 for exposed logging or smth
        # its not necessary
        return x1_new, x2_new
