.. _documenting-abipy:

Documenting AbiPy
==================

.. contents::
   :backlinks: top

Organization of documentation
-----------------------------

The documentation for AbiPy is generated from ReStructured Text using the Sphinx_ documentation generation tool. 
The documentation sources are found in the :file:`~/docs/` directory in the repository.  
To build the documentation in html format, cd into :file:`abipy/docs/` and do::

  make html 

The actual ReStructured Text files are kept in :file:`docs/users`, :file:`docs/devel`, :file:`docs/api`. 
The main entry point is :file:`docs/index.rst`, which pulls in the :file:`index.rst` 
file for the users guide, developers guide, api reference. 

Additional files can be added to the various guides by including their base
file name (the ``.rst`` extension is not necessary) in the table of contents.
It is also possible to include other documents through the use of an include
statement, such as::

  .. include:: ../../TODO

The output produced by Sphinx can be configured by editing the :file:`conf.py` file located in the :file:`docs/`.
Before building the documentation, you need to install the sphinx extensions listed 
in :file:`abipy/docs/requirements.txt` with::

    pip install -r abipy/docs/requirements.txt

* api - placeholders to automatically generate the api documentation
* devel - documentation for AbiPy developers
* users - the user documentation, e.g plotting tutorials, configuration tips, etc.
* faq - frequently asked questions
* index.rst - the top level include document for AbiPy docs
* conf.py - the sphinx configuration
* _static - used by the sphinx build system
* _templates - used by the sphinx build system

To build the HTML documentation, install sphinx then type ``make html`` that will execute::

    sphinx-build -b html -d _build/doctrees . _build/html

Remeber to issue::

    export READTHEDOCS=1

before running ``make`` to activate the generation of the thumbnails in :file:`abipy/examples/flows`.

The documentation is produced in :file:`_build/html`.

You can run ``make help`` to see information on all possible make targets.

Use ``pip`` to install the dependencies::

    pip install -r requirements.txt

To deploy to gh-pages::

   ./ghp_import.py _build/html/ -n -p

.. _formatting-abipy-docs:

Formatting
----------

The Sphinx website contains plenty of documentation_ concerning ReST markup and
working with Sphinx in general. 
Here are a few additional things to keep in mind:

* Please familiarize yourself with the Sphinx directives for `inline markup`_. 
  Abipy's documentation makes heavy use of cross-referencing and other semantic markup. 
  Several aliases are defined in :file:`abipy/docs/links.rst` and are automatically
  included in each ``rst`` file via `rst_epilog <http://www.sphinx-doc.org/en/stable/config.html#confval-rst_epilog>`_

* Function arguments and keywords should be referred to using the *emphasis* role. 
  This will keep AbiPy's documentation consistant with Python's documentation::

    Here is a description of *argument*

  Please do not use the `default role`::

    Please do not describe `argument` like this.

  nor the ``literal`` role::

    Please do not describe ``argument`` like this.

* Mathematical expressions can be rendered with `mathjax <https://www.mathjax.org/>`_ in html.
  For example:

  ``:math:`\sin(x_n^2)``` yields: :math:`\sin(x_n^2)`, and::

    .. math::

      \int_{-\infty}^{\infty}\frac{e^{i\phi}}{1+x^2\frac{e^{i\phi}}{1+x^2}}

  yields:

  .. math::

    \int_{-\infty}^{\infty}\frac{e^{i\phi}}{1+x^2\frac{e^{i\phi}}{1+x^2}}

* Bibtex citations are supported via the 
  `sphinxcontrib-bibtex extension <https://sphinxcontrib-bibtex.readthedocs.io/en/latest/>`_
  The bibtext entries are declared in the :file:`abipy/docs/refs.bib` file.
  For example::

    See :cite:`Gonze2016` for a brief description of recent developments in ABINIT.

  yelds: See :cite:`Gonze2016` for a brief description of recent developments in ABINIT.

* Interactive ipython_ sessions can be illustrated in the documentation using the following directive::

    .. sourcecode:: ipython

      In [69]: lines = plot([1, 2, 3])

  which would yield:

  .. sourcecode:: ipython

    In [69]: lines = plot([1, 2, 3])

* Use the *note* and *warning* directives, sparingly, to draw attention to important comments::

    .. note::
       Here is a note

  yields:

  .. note::
     here is a note

  also:

  .. warning::
     here is a warning

* Use the *deprecated* directive when appropriate::

    .. deprecated:: 0.98
       This feature is obsolete, use something else.

  yields:

  .. deprecated:: 0.98
     This feature is obsolete, use something else.

* Use the *versionadded* and *versionchanged* directives, which have similar
  syntax to the *deprecated* role::

    .. versionadded:: 0.2
       The transforms have been completely revamped.

  .. versionadded:: 0.2
     The transforms have been completely revamped.

* The autodoc extension will handle index entries for the API, but additional
  entries in the index_ need to be explicitly added.

.. _documentation: http://sphinx.pocoo.org/contents.html
.. _`inline markup`: http://sphinx.pocoo.org/markup/inline.html
.. _index: http://sphinx.pocoo.org/markup/para.html#index-generating-markup

Docstrings
----------

In addition to the aforementioned formatting suggestions:

* Docstrings are written following the 
  `Google Python Style Guide <http://google.github.io/styleguide/pyguide.html>`_.
  We use the `napoleon <https://sphinxcontrib-napoleon.readthedocs.io/en/latest/>`_ extension
  to convert Google style docstrings to reStructuredText before Sphinx attempts to parse them.

* Please limit the text width of docstrings to 70 characters.

* Keyword arguments should be described using a definition list.

Dynamically generated figures
-----------------------------

Figures can be automatically generated from scripts and included in the docs.  
It is not necessary to explicitly save the figure in the script, this will be done 
automatically at build time to ensure that the code that is included runs and produces the advertised figure.

Any plots specific to the documentation should be added to the ``examples/plot/`` directory and committed to git.  

`sphinx-gallery <https://github.com/sphinx-gallery/sphinx-gallery>`_
