$script = <<SCRIPT

set -e

# install PostgreSQL and PostGIS
sudo apt-get update
sudo apt-get install -y --no-install-recommends postgresql-9.4-postgis-2.1 libpq-dev

# create PostGIS database
sudo sudo -u postgres createuser -s vagrant

sudo sudo -u postgres createdb ogn -O vagrant
sudo sudo -u postgres psql -d ogn -c 'CREATE EXTENSION postgis;'

# install python requirements
cd /vagrant
sudo apt-get install -y --no-install-recommends redis-server build-essential python3 python3-pip python3-dev libpq-dev libgeos-dev
sudo -H pip3 install -r requirements.txt

# # initialize database
./manage.py db.init

# # import registered devices from ddb
./manage.py db.import_ddb

SCRIPT

Vagrant.configure("2") do |config|
  config.vm.box = 'debian/jessie64'

  # Current version is broken
  config.vm.box_version = '8.5.2'

  config.vm.provision 'shell', inline: $script, privileged: false
end
