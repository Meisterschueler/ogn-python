from flask.cli import AppGroup
import click

from datetime import datetime
from tqdm import tqdm

from app.commands.database import get_database_days
from app import db
from app.collect.flights import compute_flights, compute_gaps

user_cli = AppGroup("flights")
user_cli.help = "Create 2D flight paths from data."


@user_cli.command("create")
@click.argument("start")
@click.argument("end")
@click.argument("flight_type", type=click.INT)
def create(start, end, flight_type):
    """Compute flights. Flight type: 0: all flights, 1: below 1000m AGL, 2: below 50m AGL + faster than 250 km/h, 3: inverse coverage'"""

    days = get_database_days(start, end)

    pbar = tqdm(days)
    for single_date in pbar:
        pbar.set_description(datetime.strftime(single_date, "%Y-%m-%d"))
        if flight_type <= 2:
            result = compute_flights(date=single_date, flight_type=flight_type)
        else:
            result = compute_gaps(date=single_date)
