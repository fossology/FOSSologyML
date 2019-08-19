.. _convert_data:

Convert data in MongoDB
==================================


**Prerequisites**:
------------------


**python3.6.0 and higher**
    We suggest to install create a virtual environment see e.g: https://docs.python-guide.org/dev/virtualenvs/

**rigel in develop mode**
    Run following::

        git clone https://github.com/mcjaeger/rigel.git
        cd rigel
        pip install -e .
        pip install -r train_model/requirements.txt
        rigel-download-data

**MongoDB filled with file_raw data**
    see :ref:`import_data`


**To convert and deduplicate the data in MongoDB**::
----------------------------------------------------

Switch to the rigel directory and (if using) activate the virtual environment, then run::

    cd path/to/rigel/train_model
    python convert_data.py

whereby, if you either setup following environment variables for the active shell where you are starting the script (you can also define them in the file ``path/to/rigel/train_model/.env`` which will be scanned automatically)::

    MONGODB_HOST:                   hostname/IP
    MONGODB_PORT:                   port (mongo default: 27017)
    MONGODB_APPLICATION_DATABASE:   database name (usually rigel)
    MONGODB_APPLICATION_USERNAME:   database user
    MONGODB_APPLICATION_PASSWORD:   password for database user

or you modify the main function of the ``path/to/rigel/train_model/convert_data.py`` and pass the parameters to the constructor of MongoDB()::

    db=None, host=None, port=None, username=None, password=None):
    if __name__ == '__main__':
        logger = root_logger('convert_data', logging.INFO)
        try:
            db = MongoDB(db=rigel, host=localhost, port=27017, username=username, password=password) # your credentials for mongo db can be set up here
            convert_data(Documents.FileRaw, Documents.File)
            logger.info('Success')
        except Exception as e:
            logger.info(e, exc_info=True)
            logger.error(e)

Note that the credentials defined in the constructor have precedence over the config ``path/to/rigel/train_model/.env`` file.

If successful the sample output would be something like this::

    2018-09-21 18:12:57 - convert_data[utils] - INFO - *
    2018-09-21 18:12:57 - convert_data[utils] - INFO - *
    2018-09-21 18:12:57 - convert_data[utils] - INFO - *
    2018-09-21 18:12:57 - convert_data[root] - INFO - Connected to: {'address': ('127.0.0.1', 27017), 'database': 'rigel'}
    2018-09-21 18:12:59 - convert_data[root] - INFO - Converting: FileRaw (435) -> File (0)
    2018-09-21 18:13:00 - convert_data[utils] - INFO -  Completed 0 % (0 / 435)
    2018-09-21 18:13:00 - convert_data[utils] - INFO -  Completed 10 % (43 / 435)
    2018-09-21 18:13:00 - convert_data[utils] - INFO -  Completed 20 % (86 / 435)
    2018-09-21 18:13:00 - convert_data[utils] - INFO -  Completed 30 % (129 / 435)
    2018-09-21 18:13:00 - convert_data[utils] - INFO -  Completed 40 % (172 / 435)
    2018-09-21 18:13:01 - convert_data[utils] - INFO -  Completed 49 % (215 / 435)
    2018-09-21 18:13:01 - convert_data[utils] - INFO -  Completed 59 % (258 / 435)
    2018-09-21 18:13:01 - convert_data[utils] - INFO -  Completed 69 % (301 / 435)
    2018-09-21 18:13:01 - convert_data[utils] - INFO -  Completed 79 % (344 / 435)
    2018-09-21 18:13:01 - convert_data[utils] - INFO -  Completed 89 % (387 / 435)
    2018-09-21 18:13:01 - convert_data[utils] - INFO -  Completed 99 % (430 / 435)
    2018-09-21 18:13:01 - convert_data[root] - INFO - File count: (418)
    2018-09-21 18:13:01 - convert_data[root] - INFO - Success


**To check the contents of the MongoDB you can**
    Login to your mongo shell::

        mongo <mongo_db_name> -u <mongo_username> -p <mongo_password>

    and query::

        db.file({"_cls" : "File.Conclusion"}).count();

The output corresponding to the example above shall be ``10`` meaning, there are 10 documents after the deduplication that can be used for training the model.
