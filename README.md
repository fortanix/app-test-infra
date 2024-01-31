# README #

This repository contains the application test infrastructure code that currently runs in zircon and Salmiac.

### What is this repository for? ###

This repository is created to share the application test infrastruture code between zircon and salmiac. In future we can also use it to share between similar projects.
### How do I get set up? ###

Typically in order to share and use this, the project must have this module as its submodule. Then there should be some kind of makefile rules
and/or python and/or shell scripts that uses the test infrastructure code here. 
### Contribution guidelines ###

Any changes made here should verified by running tests in zircon(enclaveos) and nitro. Typically the way to do it would be to checkout the 
development branch of this project and then run the tests in zircon and salmiac. 

Python code guidelines:
* Sort package imports alphabetically with no sections. This can be easily done with the help of the isort tool:
  $ isort --no-sections .

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact
