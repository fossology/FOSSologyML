.. _update_data:

Update data in MongoDB
========================

Now that the raw data has been deduplicated and resides in the MongoDB (db.file collection),
we need to preprocess it and assign attributes and metadata to each of the documents,
if we want to use it for training.

**Prerequisites**:
------------------

See :ref:`import_data` and :ref:`convert_data`

**Files from FOSSology instance (same that was used to fill the MongoDB)**
    It depends on your current setup, but in the end you need to make sure, that the files are reachable under ``path/to/rigel/train_model/data/conclusions`` directory:

    The files are normally to be found under ``root@vagrant-ubuntu-trusty-64:/srv/fossology/repository/localhost/files`` and have restricted access.

    * If you run your FOSSology instance locally, you can just create a symlink
    * From FOSSology running in docker see ``docker cp``
    * From FOSSology running in vagrant box you can use ``scp`` or ``rsync``

    Note that depending on the size of all files that are being copied here can be quite big, so check the disk space beforehand.


**Optionally**
    you might want to run define *license mapping* for the licenses in MongoDB before running the update routine.

    To generate a template file as describe below run::

        python analyze_data.py

    *License mapping* is a ``license_mapping.csv`` semi-colon separated file in following format
    (each line maps one original license name to N)::

        <original_license_name1>;<here you can define new name1>; <here you can define new name2> ...
        <original_license_name2>;NO_MAPPED_LICENSE;
        <original_license_name3>;<here you can define new name1>; <here you can define new name2>;MULTI_LICENSE  ...

    There are two reserved words that define the mapping behavior

    * NO_MAPPED_LICENSE means this license will not be mapped to mapped_licenses field andthus not used for training the model
    * MULTI_LICENSE is additional mapping attribute symbolizing that the document is licensed under one OR another license (Dual Licensing)

**To update the data in MongoDB**::
----------------------------------------------------

Switch to the rigel directory and (if using) activate the virtual environment, then run::

    cd path/to/rigel/train_model
    python update_data.py

whereby, you might want to set up database connections or some other parameters (n_cores, batch_size) in main function::

    if __name__ == '__main__':
        logger = root_logger('update_data', logging.INFO)
        load_dotenv(find_dotenv())
        preprocessor = PreprocessorSpacy()

        try:
            db = MongoDB()  # credentials for MongoDB can be set up here
            n_cores = cpu_count()  # number of processors that shall be used can be set up here

            license_mapping = load_license_mapping_file(get_train_dir() / LICENSE_MAPPING_FILENAME)
            update(update_document, n_cores=n_cores, batch_size=10_000, collection=Documents.Conclusion)

            collection_analysis = analyze_in_parallel(db, n_cores=n_cores, batch_size=10_000,
                                                      collection=Documents.Conclusion)

            collection_analysis.save_statistics(db)
            collection_analysis.save_object()

        # this is useful for validation of the models later, usually the factor is around 0.1 = 10%
        # however for strongly biased sets it might be better to lessen the factor
        add_tag(collection_analysis, tag=Tag.TEST.value, min_samples=10, factor=0.1)

        except Exception as e:
            logger.info(e, exc_info=True)


After successfuly running the script notice the collection analysis file ``path/to/rigel/train_model/database_analysis/Conclusion.stat`` was created.

This file includes a basic statistical analysis of documents in MongoDB, in particular the counts of licenses are
important and used later in training to define thresholds and limits on selection of training data.