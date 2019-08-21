FOSSologyML
===========

Open Source License Classifier, driven by Machine Learning. FOSSologyML is a toolkit which introduces a new scan tool for FOSSology: rigel.

This new tool can be used as a standalone rigel-cli or started as a simple server with rigel-server. A FOSSology wrapper agent communicates then with the rigel-server. Opposed to nomos, which can be started at every scan, it is better to have rigel running, because of the longer initialisation times for the classifier.


Installation
------------

::

    pip install git+https://github.com/fossology/FOSSologyML.git

Or in a develop mode after downloading a zip or cloning the git repository ::

    git clone https://github.com/fossology/FOSSologyML.git
    cd
    pip install -e .


Once installed you need to download default model and language preprocessing data for english by running ::

    rigel-download-data

Then you can run ::

    rigel-cli --help

or ::

    rigel-server --help

Development
-----------

To start all tests run ::

    python setup.py test

To generate documentation with Sphinx run ::

    cd docs
    sphinx-apidoc ../FOSSologyML/ -f -o .
    make html

To package make sure you have the following installed ::

    pip install --user --upgrade setuptools wheel

and run ::

    python setup.py sdist bdist_wheel


How to build the model
----------------------

See `Documentation <https://>_` for info on how to build your own model and more.


License
--------
SPDX-License-Identifier: GPL-2.0-only

See the file LICENSE.rst
