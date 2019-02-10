from ogn_python import app

from .bulkimport import user_cli as bulkimport_cli
from .database import user_cli as database_cli
from .export import user_cli as export_cli
from .flights import user_cli as flights_cli
from .logbook import user_cli as logbook_cli
from .stats import user_cli as stats_cli

app.cli.add_command(bulkimport_cli)
app.cli.add_command(database_cli)
app.cli.add_command(flights_cli)
app.cli.add_command(logbook_cli)
app.cli.add_command(stats_cli)
