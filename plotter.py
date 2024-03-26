import io
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression


def generate_burndown_plot(burndown_data, sprints_simple, width=14, height=6):
    log("generating plot...")
    
    plt.figure(figsize=(width, height))
    
    ax = plt.gca()

    # add vertical lines to separate sprints and add labels below them
    for sprint in sprints_simple:

        ax.axvline(x=sprint["startDate"], color="purple")
        label_x = sprint["startDate"]
        ax.text(label_x, -10, sprint["startDate"].strftime("%Y-%m-%d"), ha="center", va="bottom", rotation=45)
        label_x = sprint["startDate"] + (sprint["endDate"] - sprint["startDate"]) / 2
        ax.text(label_x, 0, sprint["name"], ha="center", va="bottom")
        
    # add vertical line and label for the end date of the last sprint
    sprint = sprints_simple[-1]
    ax.axvline(x=sprint["endDate"], color="purple")
    label_x = sprint["endDate"]
    ax.text(label_x, -10, sprint["endDate"].strftime("%Y-%m-%d"), ha="center", va="bottom", rotation=45)

    # plot burndown line
    dates, points = zip(*burndown_data)
    ax.plot(dates, points, label="Actual", color="blue")

    # fit linear regression model
    dates_numeric = np.array([(date - dates[0]).days for date in dates]).reshape(-1, 1)
    regression_model = LinearRegression()
    regression_model.fit(dates_numeric, points)
    trend_line = regression_model.predict(dates_numeric)
    ax.plot(dates, trend_line, color="red", linestyle="-", label="Trend")

    # calculate ideal burndown line
    max_points = max(points)
    ideal_slope = -max_points / (len(dates) - 1)
    ideal_line = [max_points + ideal_slope * i for i in range(len(dates))]
    ax.plot(dates, ideal_line, color="lime", linestyle="-", label="Ideal")

    # set labels and title
    ax.set_xlabel("Time")
    ax.set_ylabel("Remaining Effort Points")
    ax.set_title("Cumulative Burndown Plot")

    # add marker for current date
    current_date = datetime.now().date()
    ax.axvline(x=current_date, color="deepskyblue", linestyle="-")
    ax.text(current_date + timedelta(1), -10, "Current Date", ha="right", va="bottom", rotation=45)

    # adjust y-axis limits to start from 0 and end at the maximum remaining points
    ax.set_ylim(0, max(points) + 100)
    
    # find the maximum end date among sprints to set x-axis limit
    max_end_date = max(sprint["endDate"] for sprint in sprints_simple)
    
    # adjust x-axis limits to provide some spacing
    ax.set_xlim(sprints_simple[0]["startDate"] - timedelta(days=3), max_end_date + timedelta(days=3))

    # remove x-axis tick labels
    ax.set_xticklabels([])

    # show legend
    ax.legend(loc="upper right")

    # show grid on plot
    plt.grid(True)
    
    log("generating plot done")
    
    return plt


def convert_plot_to_png(plot):
    log("converting plot to png...")
    
    plot.gca().set_facecolor("white")
    buffer = io.BytesIO()
    plot.savefig(buffer, format="png")
    buffer.seek(0)
    png_data = buffer.getvalue()
    
    log("converting plot to png done")
    
    return png_data


def log(message):
    print(f"\n[plotter] {message}")
