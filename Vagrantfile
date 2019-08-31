$script = <<SCRIPT

set -e

# install PostgreSQL and PostGIS
sudo apt-get update
sudo apt-get install -y postgresql-11-postgis-2.5

# create PostGIS database
sudo sudo -u postgres createuser -s vagrant

sudo sudo -u postgres createdb ogn -O vagrant
sudo sudo -u postgres psql -d ogn -c 'CREATE EXTENSION postgis;'

# install python requirements
cd /vagrant
sudo apt-get install -y python3-pip redis-server
sudo pip3 install -r requirements.txt

# # initialize database
#./manage.py db.init

# # import registered devices from ddb
#./manage.py db.import_ddb

SCRIPT

Vagrant.configure("2") do |config|
  config.vm.box = 'debian/buster64'
  config.vm.provision 'shell', inline: $script, privileged: false
end
