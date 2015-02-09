# coding: utf-8
"""Base Classes and utils for lessons."""
from __future__ import print_function, division, unicode_literals

import sys
import os
import six
import abc
import shutil

from monty.functools import lazy_property


class BaseLesson(six.with_metaclass(abc.ABCMeta, object)):

    #def __init__(self, **kwargs):
    #    self._mode = kwargs.get("mode", "ipython-shell")

    @abc.abstractproperty
    def doc_string(self):
        """docstring of the lesson."""

    @abc.abstractproperty
    def pyfile(self):
        """Path of the python script."""
        print(self.__class__.__module__)
        return self.__class__.__module__

    def get_local_copy():
        """
        Copy this script to the current working dir to explore and edit
        """
        dst = os.path.basename(self.pyfile)
        if os.path.exists(dst):
            raise RuntimeError("file %s already exists. Remove it before calling get_local_copy" % dst)
        shutil.copyfile(self.pyfile, dst)

    #def __repr__(self):
    #    s = self._pandoc_convert()
    #    if s is None: s = self.doc_string
    #    return s

    @lazy_property
    def manfile(self):
        import tempfile
        _, man_fname = tempfile.mkstemp(suffix='.man', text=True)
        with open(man_fname, 'wt') as fh: 
            fh.write(self._pandoc_convert(to="man", extra_args=("-s",)))
        return man_fname

    def _pandoc_convert(self, to, extra_args=()):
         try:
            import pypandoc
            return pypandoc.convert(self.doc_string, to, "rst", extra_args=extra_args)
         except OSError, ImportError:
            return "pypandoc.convert failed. Please install pandoc and pypandoc"

    #def publish_string(self, writer_name="manpage"):
    #    from docutils.core import publish_string, publish_parts
    #    return publish_string(self.doc_string, writer_name=writer_name)

    def _repr_html_(self):
        from docutils.core import publish_string, publish_parts
        return publish_string(self.doc_string, writer_name="html")
        #return publish_parts(self.doc_string, writer_name='html')['html_body']

    #@staticmethod
    #def abinit_help(varname):
    #    from abipy.abilab import abinit_help
    #    return abinit_help(varname)
