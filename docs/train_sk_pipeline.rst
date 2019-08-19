.. _train_sk_pipeline:

Train model with scikit learn pipeline (sklearn)
================================================


**Prerequisites**:
------------------


**python3.6.0 and higher**
    see: :ref:`convert_data`

**rigel in develop mode**
    see: :ref:`convert_data`

**MongoDB filled with updated data data**
    see:  :ref:`import_data` and :ref:`update_data`


**To train a new model**:
----------------------------------------------------

Switch to the rigel directory and (if using) activate the virtual environment, then run::

    cd path/to/rigel/train_model
    python train_sk_pipeline.py

whereby, you might want to set up database connections or some other parameters for model training in the main function::

    if __name__ == '__main__':
        logger = root_logger('train_sk_pipeline', logging.INFO)
        load_dotenv(find_dotenv())

        scenario_dir = Path(get_train_dir() / f'sklearn_{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")}')
        scenario_dir.mkdir(parents=True, exist_ok=True)
        add_file_handler_to_logger(logger, scenario_dir, 'train_sk_pipeline')

        try:
            db = MongoDB()  # credentials for MongoDB can be set up here
            n_cores = cpu_count()  # number of processors that shall be used for loading data from MongoDB
            max_samples = 10_000  # max number of samples per license, used for single and multi label problem, value
            min_samples = 1_000  # min number of samples per license, decides if the license will be taken to training, internally limited to 10

            collection_analysis = CollectionAnalysis.load_object(get_db_analysis_dir() / 'Conclusion.pkl')

            training_licenses = collection_analysis.get_mapped_licenses_with_min_samples(min_samples)

            data_loader = DataLoaderCustom(scenario_dir)
            pipeline = SKLearnPipeline(ConfigParser(), data_loader)

            train_sk_pipeline(pipeline,
                              max_samples=max_samples,
                              train_in_parallel=True,
                              exclude_data_for_benchmark=True)

        except Exception as e:
            logger.exception(e)


Each new run of the script will make a new subdirectory with the timestamp, model data, model configuration file and
The final structure of the ready model looks like this::

    sklearn_2018_09_22_06_01/
    ├── DP                      :: "dual problem" - the single vs multi vs no license
    ├── licenses                :: license texts to all licenses from MongoDB, on which this model was trained
    ├── MP                      :: multi label problem
    ├── SP                      :: single label problem
    ├── conf.ini                :: configuration file
    └── train_sk_pipeline.log   :: training log


To use the model as a default model for rigel, copy it under rigel's model directory
(typically ``$HOME/rigel/models``) and rename it to ``default model``

Alternatively if you are using rigel-cli for the prediction, or rigel-server in development mode
you can specify the path to the model directory with ``-m`` option.