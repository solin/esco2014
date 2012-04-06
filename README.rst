
ESCO conference web site
========================

Updating Dreamhost
------------------

If this is your first time updating Dreamhost, issue the following command::

    $ git remote add <username> https://<username>@github.com/femhub/femtec.git

(use your username at GitHub in place of ``<username>``). We use this approach
to avoid storing private SSH keys at Dreamhost. Note that every remote command
you issue will require your to type password to your GitHub account.

Else issue::

    $ git fetch <username>
    $ git pull <username> master

If you didn't change web site configuration, any ``*.py`` files or templates,
then you are done. Otherwise you have to restart Passenger daemon. The simplest
way to achieve this is to issue::

    $ killall python

Note that this will forcibly terminate all instances of Python's interpreter,
which isn't a problem with current configuration, but is a subject for future
refinement.
