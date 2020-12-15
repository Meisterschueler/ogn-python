from app import db
from app.model import DirectionStatistic
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


def create_range_figure2(sender_id):
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    xs = range(100)
    ys = [random.randint(1, 50) for x in xs]
    axis.plot(xs, ys)

    return fig


def create_range_figure(sender_id):
    sds = db.session.query(DirectionStatistic) \
        .filter(DirectionStatistic.sender_id == sender_id) \
        .order_by(DirectionStatistic.directions_count.desc()) \
        .limit(1) \
        .one()

    fig = Figure()

    direction_data = sds.direction_data
    max_range = max([r['max_range'] / 1000.0 for r in direction_data])

    theta = np.array([i['direction'] / 180 * np.pi for i in direction_data])
    radii = np.array([i['max_range'] / 1000 if i['max_range'] > 0 else 0 for i in direction_data])
    width = np.array([13 / 180 * np.pi for i in direction_data])
    colors = plt.cm.viridis(radii / max_range)

    ax = fig.add_subplot(111, projection='polar')
    ax.bar(theta, radii, width=width, bottom=0.0, color=colors, edgecolor='b', alpha=0.5)
    #ax.set_rticks([0, 25, 50, 75, 100, 125, 150])
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)

    fig.suptitle(f"Range between sender '{sds.sender.name}' and receiver '{sds.receiver.name}'")

    return fig
