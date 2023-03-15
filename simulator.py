import math
import random

class MovementCurve:

    def __init__(self):

        self.ease_out_quad = lambda x: -x * (x - 2)

    def GetInternalKnots(self, start, end):

        left, right = min(start[0], end[0]), max(start[0], end[0])
        top, bottom = min(start[1], end[1]), max(start[1], end[1])

        internal_knots = []
        for idx in range(2):
            x = random.randint(left - 50, right + 50)
            y = random.randint(top - 50, bottom + 50)
            internal_knots.append((x, y))

        return internal_knots

    def BernsteinPolynomial(self, knots, factor):

        x, y, degree = 0, 0, len(knots) - 1
        for idx, knot in enumerate(knots):
            binomial = math.factorial(degree) / float(math.factorial(idx) * math.factorial(degree - idx))
            polynomial = binomial * (factor ** idx) * ((1 - factor) ** (degree - idx))
            x += knot[0] * polynomial
            y += knot[1] * polynomial

        return x, y

    def BezierCurve(self, knots, points_count):

        points = []
        for idx in range(points_count):
            factor = idx / (points_count - 1)
            point = self.BernsteinPolynomial(knots, factor)
            points.append(point)

        return points

    def DistortPoints(self, points):

        mean, std, frequency = 1, 1, 0.5
        distorted_points = []
        for point in points[1:-1]:
            delta = random.gauss(mean, std) if random.random() < frequency else 0
            distorted_points.append((point[0], point[1] + delta))

        distorted_points = [points[0], *distorted_points, points[-1]]

        return distorted_points

    def TweenPoints(self, points):

        target_points = random.randint(37, 87)
        tweened_points = []

        for idx in range(target_points):
            point_idx = int(self.ease_out_quad(float(idx) / (target_points - 1)) * (len(points) - 1))
            tweened_points.append(points[point_idx])

        return tweened_points

    def Generate(self, start, end):

        internal_knots = self.GetInternalKnots(start, end)
        knots = [start, *internal_knots, end]
        points_count = max(abs(start[0] - end[0]), abs(start[1] - end[1]), 2)

        points = self.BezierCurve(knots, points_count)
        points = self.DistortPoints(points)
        points = self.TweenPoints(points)

        return points

class Simulator:

    def __init__(self):

        self.movement_curve = MovementCurve()

    def GetMouseMovements(self, start, end):

        movements = []
        points = self.movement_curve.Generate(start, end)
        for x, y in points[1:-1]:
            delay = random.uniform(0.008, 0.018)
            movements.append([round(x), round(y), delay])

        movements.append([*end, 0])
        return movements

    def GetClickDelays(self, click_count):

        delays = []
        for iteration in range(click_count):
            button_down_delay = random.uniform(0.063, 0.151)
            inter_click_delay = random.uniform(0.054, 0.340) if iteration < click_count - 1 else 0
            delays.append([button_down_delay, inter_click_delay])

        return delays

    def GetPressDelays(self, press_count):

        delays = []
        for iteration in range(press_count):
            button_down_delay = random.uniform(0.037, 0.087)
            inter_press_delay = random.uniform(0.097, 0.332) if iteration < press_count - 1 else 0
            delays.append([button_down_delay, inter_press_delay])

        return delays

    def GetWheelDeltas(self, start_y, end_y):

        delta_choices = [-100, 100, 200, 300]
        delta_weights = [0.02, 0.73, 0.20, 0.05]
        mean_delay, std_delay = 0.063, 0.088
        min_delay, max_delay = 0.001, 0.275

        if start_y < end_y:
            sign, not_stop = 1, lambda start_y, end_y: start_y < end_y
        else:
            sign, not_stop = -1, lambda start_y, end_y: start_y > end_y

        deltas = []
        while not_stop(start_y, end_y):
            delta = random.choices(delta_choices, weights=delta_weights, k=1)[0] * sign
            delay = random.gauss(mean_delay, std_delay)
            delay = min(max(delay, min_delay), max_delay)
            deltas.append([delta, delay])
            start_y += delta

        return deltas

    def GetMoveClickDelay(self):

        return random.uniform(0.054, 0.280)

    def GetPressClickDelay(self):

        return random.uniform(0.121, 1.437)

    def GetReactionDelay(self):

        return random.uniform(1.196, 2.738)

    def GetClickPosition(self, width, height):

        center_width = 0.8 * width
        mean_x, std_x = 0.5 * center_width, 0.17 * center_width
        x = random.gauss(mean_x, std_x)
        x = min(max(0, x), center_width)
        x = round(0.1 * width) + int(x)

        center_height = 0.8 * height
        mean_y, std_y = 0.5 * center_height, 0.17 * center_height
        y = random.gauss(mean_y, std_y)
        y = min(max(0, y), center_height)
        y = round(0.1 * height) + int(y)

        return x, y
