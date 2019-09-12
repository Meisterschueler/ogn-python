from .database import user_cli as database_cli
from .export import user_cli as export_cli
from .flights import user_cli as flights_cli
from .gateway import user_cli as gateway_cli
from .logbook import user_cli as logbook_cli
from .stats import user_cli as stats_cli

def register(app):
    app.cli.add_command(database_cli)
    app.cli.add_command(export_cli)
    app.cli.add_command(flights_cli)
    app.cli.add_command(gateway_cli)
    app.cli.add_command(logbook_cli)
    app.cli.add_command(stats_cli)
