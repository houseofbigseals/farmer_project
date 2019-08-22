
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
            name: str,
            time: float = None
    ):
        self.x1 = x1
        self.x2 = x2
        self.time = time
        self.result = result
        self.name = name


class TableSearch(object):
    """
    This object contains table with fixed number of points
    to search with with predetermined coordinates
    After search the worker must wait delay_after_search time
    """
    def __init__(
            self
    ):
        # logger
        self.logger = logging.getLogger("Worker.SearchMethods.TableSearchMethod")
        # self.schedule = [
        #     [700, 0, "1", 10],
        #     [200, 0, "2", 10],
        #     [450, 0, "3", 10],
        #     [700, 1, "4", 10],
        #     [200, 1, "5", 10],
        #     [450, 1, "6", 10],
        #     [700, 1.5, "7", 10],
        #     [200, 1.5, "8", 10],
        #     [450, 1.5, "9", 10],
        #     [700, 1, "4", 10],   #  ------------------- repeating
        #     [450, 1, "6", 10],
        #     [200, 1, "5", 10],
        #     [450, 1.5, "9", 10],
        #     [700, 1.5, "7", 10],
        #     [200, 1.5, "8", 10],
        #     [700, 0, "1", 10],
        #     [450, 0, "3", 10],
        #     [200, 0, "2", 10]
        # ]
        self.schedule = [
            [500, 1.25, '6', 10],
            [500, 0, '1', 10],
            [500, 1, '5', 10],
            [500, 0.5, '3', 10],
            [500, 0.75, '4', 10],
            [500, 0.25, '2', 10],
            [500, 1.5, '7', 10]
        ]
        self.search_table = []
        # lets reformat schedule table to SearchPoint
        for i in self.schedule:
            new_point = SearchPoint(
                x1=i[0],
                x2=i[1],
                name=i[2],
                time=i[3],
                result=0
            )
            self.search_table.append(new_point)

        self.logger.info("Method started")

    def do_search_step(self):
        """
        unlike real search methods, this method just clears search table and starts again
        :return:
        """
        for p in self.search_table:
            p.result = 0

        return self.search_table[0].x1, self.search_table[0].x2


class StaticSearch(object):
    """
    This object contains table with only one point
    to search with with predetermined coordinates
    After search the worker must wait delay_after_search time
    """
    def __init__(
            self
    ):
        # logger
        self.logger = logging.getLogger("Worker.SearchMethods.StaticSearchMethod")
        self.schedule = [
            [500, 1.5, 'the_only_one', 10]
        ]
        self.search_table = []
        # lets reformat schedule table to SearchPoint
        for i in self.schedule:
            new_point = SearchPoint(
                x1=i[0],
                x2=i[1],
                name=i[2],
                time=i[3],
                result=0
            )
            self.search_table.append(new_point)

        self.logger.info("Method started")

    def do_search_step(self):
        """
        unlike real search methods, this method just clears search table and starts again
        :return:
        """
        for p in self.search_table:
            p.result = 0

        return self.search_table[0].x1, self.search_table[0].x2


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
        # F is quality coefficient for moon base Q
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


class SimpleGradientMethod(object):
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
            h1: float = 10,
            h2: float = 0.005,
            lamb1: float = 0.1,
            lamb2: float = 0.01,
            max_x1: float = 700,
            max_x2: float = 1.5,
            min_x1: float = 200,
            min_x2: float = 0
    ):
        # suppose we need to contain three values to calculate dF/dx
        # F(x1i, x2i), F(x1i + h, x2i), F(x1i, x2i + h)
        # x1 is summ FAR intensity and is about 200-700
        # x2 is intensity of red lite to intensity of white lite and is about 0-1.5 (0-3?)
        # F is quality coefficient for moon base Q
        # logger
        self.logger = logging.getLogger("Worker.SearchMethods.SimpleGradientMethod")
        # search constant parameters
        self.lamb1 = lamb1
        self.lamb2 = lamb2
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
        x1_new = self.x1 - self.lamb1 * ((self.dFx1.result - self.dF.result) / self.h1)
        x2_new = self.x2 - self.lamb2 * ((self.dFx2.result - self.dF.result) / self.h2)
        self.logger.info("raw new search coordinates is x1 = {} x2 = {}".format(
            x1_new, x2_new
        ))
        # then lets do some security checks
        # for example, lets check if we are outside the range of acceptable values
        self.logger.info("check new coords if they are out of the range of permissible values")
        if x1_new < self.min_x1:
            # lets set x1 as lower acceptable limit
            x1_new = self.min_x1
            self.logger.info("x1_new < self.min_x1 so new x1 is {}".format(
                x1_new
            ))
        elif x1_new > self.max_x1:
            # lets set x1 as higher acceptable limit
            x1_new = self.max_x1
            self.logger.info("x1_new > self.max_x1 so new x1 is {}".format(
                x1_new
            ))

        if x2_new < self.min_x2:
            # lets set x2 as lower acceptable limit
            x2_new = self.min_x2
            self.logger.info("x2_new < self.min_x2 so new x2 is {}".format(
                x2_new
            ))
        elif x2_new > self.max_x2:
            # lets set x2 as higher acceptable limit
            x2_new = self.max_x2
            self.logger.info("x2_new > self.max_x2 so new x2 is {}".format(
                x2_new
            ))

        self.logger.info("check new coords if they with added dx1 and dx2 are "
                         "out of the range of permissible values")

        if x1_new + self.h1 > self.max_x1:
            # lets set x2 as lower acceptable limit
            x1_new = self.max_x1 - self.h1
            self.logger.info("x1_new + dh1 > self.max_x1 so new x1 is {}".format(
                x1_new
            ))
        if x2_new + self.h2 > self.max_x2:
            # lets set x2 as lower acceptable limit
            x2_new = self.max_x2 - self.h2
            self.logger.info("x2_new + dh2 > self.max_x2 so new x2 is {}".format(
                x2_new
            ))

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
        self.logger.info("new search table recalculated")
        self.logger.info("done search step from x1 = {} x2 = {} to x1 = {} x2 = {}".format(
            x1_old, x2_old, x1_new, x2_new
        ))
        # return new x1 and x2 for exposed logging or smth
        # its not necessary
        return x1_new, x2_new





class NelderMeadSearch(object):

    def __init__(self):
        pass

    def triangle_step(self, p1, p2, p3, t, alpha, beta, gamma):
        # print("triangle step")
        dt = self.param['dt']
        # print("noized functional values calculation")
        f1 = self.scalar_calc_functional(p1[0], p1[1], t)
        f2 = self.scalar_calc_functional(p2[0], p2[1], t + dt)
        f3 = self.scalar_calc_functional(p3[0], p3[1], t + 2 * dt)
        # print("calculated values are {} {} {}".format( f1, f2, f3))
        # lets make them numpy vectors
        x1 = np.array(p1)
        x2 = np.array(p2)
        x3 = np.array(p3)
        xs = [x1, x2, x3]
        n_min = int(np.argmin([f1, f2, f3]))
        # print("n min is {}".format(n_min))
        n_max = int(np.argmax([f1, f2, f3]))
        # print("n max is {}".format(n_max))
        num = [0, 1, 2]
        num.remove(n_min)
        # print(num)
        num.remove(n_max)
        n_av = num[0]
        # print(num)
        # print("n av is {}".format(n_av))
        x_min = xs[n_min]
        x_max = xs[n_max]
        # find middlepoint of triangle
        x_mid = 0.5 * (x1 + x2 + x3 - x_max)
        # reflection
        x5 = x_mid + alpha * (x_mid - x_max)
        # stretching
        f5 = self.scalar_calc_functional(x5[0], x5[1], t + 3 * dt)
        if (f5 <= min([f1, f2, f3])):
            x6 = x_mid + gamma * (x5 - x_mid)
            f6 = self.scalar_calc_functional(x6[0], x6[1], t + 4 * dt)
            if (f6 < min([f1, f2, f3])):
                return x6, xs[n_min], xs[n_av], x_mid
            else:
                return x5, xs[n_min], xs[n_av], x_mid
        # compression
        if (f5 > [f1, f2, f3][n_min] and f5 > [f1, f2, f3][n_av] and f5 < [f1, f2, f3][n_max]):
            x6 = x_mid + beta * (x_max - x_mid)
            return x6, xs[n_min], xs[n_av], x_mid
        # reduction
        if (f5 >= [f1, f2, f3][n_max]):
            x11 = x_min + 0.5 * (x1 - x_min)
            x21 = x_min + 0.5 * (x2 - x_min)
            x31 = x_min + 0.5 * (x3 - x_min)
            return x11, x21, x31, x_mid

        return x5, xs[n_min], xs[n_av], x_mid