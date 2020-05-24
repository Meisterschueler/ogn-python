from flask.cli import AppGroup
import click

from datetime import datetime

from app.collect.logbook import update_entries as logbook_update_entries
from app.collect.takeoff_landings import update_entries as takeoff_landings_update_entries
from app.model import Airport, Logbook
from sqlalchemy.sql import func
from tqdm import tqdm
from app.commands.database import get_database_days
from app.utils import date_to_timestamps

from app import db

user_cli = AppGroup("logbook")
user_cli.help = "Handling of logbook data."


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
        result = takeoff_landings_update_entries(session=db.session, start=start, end=end)


@user_cli.command("compute_logbook")
@click.argument("start")
@click.argument("end")
def compute_logbook(start, end):
    """Compute logbook."""

    days = get_database_days(start, end)

    pbar = tqdm(days)
    for single_date in pbar:
        pbar.set_description(single_date.strftime("%Y-%m-%d"))
        result = logbook_update_entries(session=db.session, date=single_date)
