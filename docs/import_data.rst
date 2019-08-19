.. _import_data:

Import raw data from FOSSology Instance
==========================================


**Prerequisites**:
------------------

**MongoDB**
    Running `MongoDB <https://www.mongodb.com/>`_ listening at <mongo_host>:27017.

    Install it on your system or alternatively fire up the docker container with ``rigel/scripts/create_docker_mongodb.sh``.
    Note that if you are using this way you should first change the credentials in the ``rigel/train_model/example.env`` file and rename it to ``.env``
    This file is not checked in version control system to protect the credentials.


**To dump the data switch to your FOSSology instance:**
-------------------------------------------------------

Following was tested in the FOSSology vagrantbox  based on Ubuntu Server 14.04 LTS (Trusty Tahr) ``config.vm.box = "trusty64"``

Currently you will have to apply the patch from https://patch-diff.githubusercontent.com/raw/maxhbr/fossology/pull/6.patch and run::

    cd /path/to/fossology/sources/
    make cli

Run the following to install mongodb php driver and library::

    cd /path/to/fossology/sources/
    sudo apt-get install php5-dev
    sudo pecl install mongodb
    echo "extension=mongodb.so" | sudo tee -a `php --ini | grep "Loaded Configuration" | sed -e "s|.*:\s*||"`
    composer require mongodb/mongodb

And start the dump with::

    ./cli/fo_dump_to_mongodb --username <fossology_username> --password <fossology_password> --mongohost <mongo_host> --mongousername <mongo_username> --mongopassword <mongo_password>

whereby::

  --username username      :: your fossology username
  --password password      :: your fossology password
  --mongohost host         :: host IP for your mongodb, which needs to be running when you dump
  --mongousername username :: username for mongo db
  --mongopassword password :: password for mongo db
  --mongodb databaseName   :: name of the database in mongo db (defaults to rigel)
  --groupIds id,id,id      :: Ids of groups, from which decisions should be used (by default all decisions are used)


The sample output of where the script dumped 25 conclusions and 410 License definitions (License definitions are always dumped as last) looks like this::

    Handle upload_pk=[2] (uploadtree_pk=[])write data with size=25 via bulk to db
    Inserted 25 documents
    write data with size=410 via bulk to db
    Inserted 410 documents


**To check the contents of the MongoDB you can:**

    Switch to the machine where your MongoDB is running and login to your mongo shell::

        mongo <mongo_db_name> -u <mongo_username> -p <mongo_password>

    and query::

        db.file_raw({}).count();

The output corresponding to the example above shall be ``25 + 410 = 435``.

Note that due to FOSSology architecture, this data is not deduplicated
e.g. if the file was scanned multiple times and/or there are more concluded licenses there will be multiple
entries for the same file in the database. Therefore the conversion step takes place next.