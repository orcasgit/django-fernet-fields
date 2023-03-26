CHANGES
=======

master (unreleased)
-------------------

0.6 (2019.05.10)
----------------

* Support Postgres 10
* Drop support for Django < 1.11, Python 3.3/3.4
* Add support for Django 1.11 through 2.2, Python 3.7

0.5 (2017.02.22)
----------------

* Support Django 1.10.

0.4 (2015.09.18)
----------------

* Add `isnull` lookup.


0.3 (2015.05.29)
----------------

* Remove DualField and HashField. The only cases where they are useful, they
  aren't secure.


0.2.1 (2015.05.28)
------------------

* Fix issue getting IntegerField validators.


0.2 (2015.05.28)
----------------

* Extract HashField for advanced lookup needs.


0.1 (2015.05.27)
----------------

* Initial working version.
