===========================
Performance Testing for NDB
===========================

Run the tests
-------------

::

    $ python3 runtests.py <base_url>

Where `base_url` is URL where the test application is deployed.

Set up your project and create indexes
--------------------------------------

You will need a service account for a Google project with either Datastore or
Firestore in Datastore mode, and will need to have downloaded the JSON
credentials for that service account. Then::

    $ source gcloud.sh <path/to/credentials/json>
    $ gcloud datastore indexes create index.yaml

Run the test application locally
--------------------------------

This will run the test application locally, using Google Cloud Datastore.
Assumes ``gcloud.sh`` has been run as shown above, which sets
``GOOGLE_APPLICATION_CREDENTIALS``, needed by the test application.

::

    $ virtualenv -p `which python3.7` venv
    $ venv/bin/pip install -r requirements.txt
    $ FLASK_APP=main venv/bin/flask run

You can also substitute ``python2.7`` for ``python3.7`` above. Performance has
not been observed to be significantly different between Python versions.

Run the tests, in a separate shell::

    $ python3 runtests.py http://localhost:5000

Using the Datastore Emulator
============================

You can also run against the local Datastore Emulator. Assuming your
application is installed locally, as above, in one shell:

::

    $ gcloud beta emulators datastore start

In the shell you're using to run the app::

    $ `gcloud beta emulators datastore env-init`
    $ FLASK_APP=main venv/bin/flask run

Run tests as before.

Deploy test app to App Engine with python37 runtime
---------------------------------------------------

::

    $ source gcloud.sh <path/to/credentials/json>
    $ ln -sf app.yaml-3.7 app.yaml
    $ gcloud app deploy


Deploy test app to App Engine with python27 runtime
---------------------------------------------------

::

    $ source gcloud.sh <path/to/credentials/json>

You really just need to run a Python 2.7 version of ``pip``. One way to do this
is to make sure your local virtual environment is using Python 2.7::

    $ rm -rf venv
    $ virtualenv -p `which python2.7` venv
    $ venv/bin/pip install -t lib -r requirements-python27.txt

Note that ``requirements.txt``, used everywhere else, installs
``google-cloud-ndb`` by pulling the ``master`` branch from the Git repository
on GitHub. To deploy to the ``python27`` runtime on App Engine, we have
to "install" our dependencies locally in the ``lib`` folder, so they can be
copied to App Engine during the deployment. Pip, however, breaks if you try to
check out a package from version control while using the ``-t`` option, so for
this step we have to use a version of ``requirements.txt``,
``requirements-python27.txt``, that install the released version from PyPi. i

In order to use an unreleased version of NDB for this deployment, you can
checkout Google Cloud NDB from git in a separate folder and then::

    $ rm -r lib/google/cloud/ndb
    $ ln -s <path/to/checkout/of/cloud-ndb>/google/cloud/ndb lib/google/cloud

Then continue with the deployment::

    $ ln -sf app.yaml-2.7 app.yaml
    $ ln -sf appengine_config.py-2.7 appengine_config.py
    $ gcloud app deploy

Deploy using Legacy NDB
=======================

You can also deploy to the ``python27`` runtime using the legacy App Engine
NDB instead of Google Cloud NDB. By setting the ``LEGACY_NDB``
environment variable to ``True``, you can arrange for the test application to
use legacy NDB instead of Cloud NDB. The easiest way to do this is just link to
``app.yaml-legacy``. Assuming you've already run the above steps::

    $ ln -sf app.yaml-legacy app.yaml
    $ gcloud app deploy
