from flask_nav import Nav
from flask_nav.elements import *

nav = Nav()

# registers the "top" menubar
nav.register_element('top_menubar', Navbar(
    View('Home', 'index'),
    View('Devices', 'devices'),
    View('Receivers', 'receivers'),
    View('Airports', 'airports'),
    View('Logbook', 'logbook'),
    View('Records', 'records'),
))
