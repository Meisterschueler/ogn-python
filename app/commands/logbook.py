from flask.cli import AppGroup
import click

from datetime import datetime

from app.collect.logbook import update_takeoff_landings, update_logbook
from app.model import Airport, Logbook
from sqlalchemy.sql import func
from tqdm import tqdm
from app.commands.database import get_database_days
from app.utils import date_to_timestamps

user_cli = AppGroup("logbook")
user_cli.help = "Handling of takeoff/landings and logbook data."


@user_cli.command("compute_takeoff_landing")
@click.argument("start")
@click.argument("end")
def compute_takeoff_landing(start, end):
    """Compute takeoffs and landings."""

    days = get_database_days(start, end)

    pbar = tqdm(days)
    for single_date in pbar:
        pbar.set_description(datetime.strftime(single_date, "%Y-%m-%d"))
        (start, end) = date_to_timestamps(single_date)
        result = update_takeoff_landings(start=start, end=end)


@user_cli.command("compute_logbook")
@click.argument("start")
@click.argument("end")
def compute_logbook(start, end):
    """Compute logbook."""

    days = get_database_days(start, end)

    pbar = tqdm(days)
    for single_date in pbar:
        pbar.set_description(single_date.strftime("%Y-%m-%d"))
        result = update_logbook(date=single_date)
