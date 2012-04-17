from __future__ import with_statement

import os
import re
import htmlentitydefs
import shutil
import subprocess

from femtec.settings import MEDIA_ROOT

class Latexible(object):

    def __unicode__(self):
        return self.to_latex()

    def to_latex(self):
        raise NotImplementedError

def convert_html_entities(s):
    matches = re.findall("&#\d+;", s)
    if len(matches) > 0:
        hits = set(matches)
        for hit in hits:
            name = hit[2:-1]
            try:
                entnum = int(name)
                s = s.replace(hit, unichr(entnum))
            except ValueError:
                pass

    matches = re.findall("&#[xX][0-9a-fA-F]+;", s)
    if len(matches) > 0:
        hits = set(matches)
        for hit in hits:
            hex = hit[3:-1]
            try:
                entnum = int(hex, 16)
                s = s.replace(hit, unichr(entnum))
            except ValueError:
                pass

    s = s.replace("&quot;", "")
    s = s.replace("&amp;", "&")
    return s 

class TocAuthors(Latexible):

    _template = u", "

    def __init__(self, authors):
        self.authors = authors

    def to_latex(self):
        single_author = len(self.authors) == 1
        return self._template.join([ author.to_latex(single_author) for author in self.authors ])

class PresentingAuthors(Latexible):

    _template = u", "

    def __init__(self, authors):
        self.authors = authors

    def to_latex(self):
        single_author = len(self.authors) == 1
        return self._template.join([ author.to_latex(single_author) for author in self.authors ])

class PresentingAuthor(Latexible):

    _template = u"""%(person)s
    %(address)s\\\\
    """
    _presenting_person = u"{%(first_name)s %(last_name)s}"
    _nonpresenting_person = u"%(first_name)s %(last_name)s"

    def __init__(self, first_name, last_name, address, email, presenting):
        self.first_name = first_name
        self.last_name = last_name
        self.address = address
        self.email = email
        self.presenting = presenting

    def to_latex(self, single_author=False):
        if not single_author and self.presenting == 'yes':
            person_template = self._presenting_person
        else:
            person_template = self._nonpresenting_person

        person = person_template % dict(
            first_name=self.first_name,
            last_name=self.last_name)

        return self._template % dict(
            person=person,
            address=self.address,
            email=self.email)

    @classmethod
    def from_json(cls, data):
        first_name = data.get('first_name', "")
        last_name = data.get('last_name', "")
        address = data.get('address', "")
        email = data.get('email', "")
        presenting = data['presenting']
        return cls(first_name, last_name, address, email, presenting)

class TocAuthor(Latexible):

    _template = u"%(person)s"
    _presenting_person = u"\\underline{%(first_name)s %(last_name)s}"
    _nonpresenting_person = u"%(first_name)s %(last_name)s"

    def __init__(self, first_name, last_name, address, email, presenting):
        self.first_name = first_name
        self.last_name = last_name
        self.address = address
        self.email = email
        self.presenting = presenting

    def to_latex(self, single_author=False):
        if not single_author and self.presenting == 'yes':
            person_template = self._presenting_person
        else:
            person_template = self._nonpresenting_person

        person = person_template % dict(
            first_name=self.first_name,
            last_name=self.last_name)

        return self._template % dict(
            person=person,
            address=self.address,
            email=self.email)

    @classmethod
    def from_json(cls, data):
        first_name = data.get('first_name', "")
        last_name = data.get('last_name', "")
        address = data.get('address', "")
        email = data.get('email', "")
        presenting = data['presenting']
        return cls(first_name, last_name, address, email, presenting)

class Author(Latexible):

    _template = u"""\
{\\large %(person)s}\\\\
%(address)s\\\\
{\\tt %(email)s}
"""
    _presenting_person = u"\\underline{%(first_name)s %(last_name)s}"
    _nonpresenting_person = u"%(first_name)s %(last_name)s"

    def __init__(self, first_name, last_name, address, email, presenting):
        self.first_name = first_name
        self.last_name = last_name
        self.address = address
        self.email = email
        self.presenting = presenting

    def to_latex(self, single_author=False):
        if not single_author and self.presenting == 'yes':
            person_template = self._presenting_person
        else:
            person_template = self._nonpresenting_person

        person = person_template % dict(
            first_name=self.first_name,
            last_name=self.last_name)

        return self._template % dict(
            person=person,
            address=self.address,
            email=self.email)

    @classmethod
    def from_json(cls, data):
        first_name = data.get('first_name', "")
        last_name = data.get('last_name', "")
        address = data.get('address', "")
        email = data.get('email', "")
        presenting = data['presenting']
        return cls(first_name, last_name, address, email, presenting)

class Authors(Latexible):

    _template = u"\\\\ \\vspace{4mm}"

    def __init__(self, *authors):
        self.authors = authors

    def to_latex(self):
        single_author = len(self.authors) == 1
        return self._template.join([ author.to_latex(single_author) for author in self.authors ])

    @classmethod
    def from_json(cls, data):
        return cls(*[ Author.from_json(author) for author in data ])

class BibAuthor(Latexible):

    _template = u"%(first_name)s %(last_name)s"

    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name

    def to_latex(self):
        return self._template % dict(
            first_name=self.first_name,
            last_name=self.last_name)

    @classmethod
    def from_json(cls, data):
        first_name = data['first_name']
        try:
            last_name = data['last_name']
        except KeyError:
            last_name = ""
        return cls(first_name, last_name)

class BibAuthors(Latexible):

    _template = u" and "

    def __init__(self, *authors):
        self.authors = authors

    def to_latex(self):
        return self._template.join([ author.to_latex() for author in self.authors ])

    @classmethod
    def from_json(cls, data):
        return cls(*[ BibAuthor.from_json(author) for author in data ])

class BibItem(Latexible):

    _template = u"""
\\bibitem{%(bibid)s}
{\\sc %(authors)s}. {%(title)s}. %(other)s.
"""

    def __init__(self, bibid, authors, title, other):
        self.bibid = bibid
        self.authors = authors
        self.title = title
        self.other = other

    def to_latex(self):
        return self._template % dict(
            bibid=self.bibid,
            authors=self.authors.to_latex(),
            title=self.title,
            other=self.other)

    @classmethod
    def from_json(cls, data):
        bibid = data['bibid']
        authors = BibAuthors.from_json(data['authors'])
        title = data['title']
        other = data['other']
        return cls(bibid, authors, title, other)

class BibItems(Latexible):

    _template = u"\n\n"

    def __init__(self, *bibitems):
        self.bibitems = bibitems

    def to_latex(self):
        return self._template.join([ bibitem.to_latex() for bibitem in self.bibitems ])

    @classmethod
    def from_json(cls, data):
        return cls(*[ BibItem.from_json(bibitem) for bibitem in data ])

class Abstract(Latexible):

    _template_abstracts = u"""
\\title{%(title)s}
\\section*{Abstract}
%(abstract)s"""

    _template_presenting = u"%(authors)s"

    _template = u"""
\\documentclass[article,A4,11pt]{llncs}
\\usepackage[T1]{fontenc}
\\usepackage{amsmath}
\\usepackage{amssymb}
\\usepackage{epsf,times}
\\usepackage{amsfonts}
\\usepackage{graphicx}
\\usepackage{mathrsfs}
\\usepackage{wrapfig}
\\usepackage{color}
\\usepackage{amsmath,mathrsfs,bm}
\\usepackage{cases}
\\usepackage{subfig}

\\leftmargin=0.2cm
\\oddsidemargin=1.2cm
\\evensidemargin=0cm
\\topmargin=0cm
\\textwidth=15.5cm
\\textheight=21.5cm
\\pagestyle{plain}
\\begin{document}

\\title{%(title)s}
\\author{} \\tocauthor{%(tocauthors)s} \\institute{}
\\maketitle
\\begin{center}
%(authors)s
\end{center}

\\section*{Abstract}

%(abstract)s

\\bibliographystyle{plain}
\\begin{thebibliography}{10}
%(bibitems)s
\\end{thebibliography}

\\end{document}
"""

    def __init__(self, title, authors, abstract, bibitems):
        self.title = title.replace('\n', '').replace('\r', '')
        self.authors = authors
        self.abstract = abstract.replace('\n', '').replace('\r', '')
        self.abstract = convert_html_entities(self.abstract)
        self.bibitems = bibitems
        temp_authors = [TocAuthor(author.first_name, author.last_name, author.address, author.email, author.presenting) for author in self.authors.authors]
        self.tocauthors = TocAuthors(temp_authors)
        temp_presenting = []
        for author in self.authors.authors:
            if author.presenting == "yes":
                temp_presenting.append(PresentingAuthor(author.first_name, author.last_name, author.address, author.email, author.presenting))
        self.presenting = PresentingAuthors(temp_presenting)

    def to_latex(self):
        return self._template % dict(
            title=self.title,
            authors=self.authors.to_latex(),
            tocauthors=self.tocauthors.to_latex(),
            abstract=self.abstract,
            bibitems=self.bibitems.to_latex())

    def to_latex_raw(self):
        return self._template_abstracts % dict(title=self.title, abstract=self.abstract)

    def to_latex_presenting(self):
        return self._template_presenting % dict(authors=self.presenting)

    @classmethod
    def from_json(cls, data):
        title = data['title']
        authors = Authors.from_json(data['authors'])
        abstract = data['abstract']
        bibitems = BibItems.from_json(data['bibitems'])
        return cls(title, authors, abstract, bibitems)

    def build_raw(self):
        return self.to_latex_raw()

    def build_presenting(self):
        return self.to_latex_presenting()

    def build(self, cwd):
        if os.path.exists(cwd):
            shutil.rmtree(cwd, True)

        os.mkdir(cwd)
        shutil.copy(
            os.path.join(MEDIA_ROOT, 'tex', 'llncs.cls'),
            os.path.join(cwd, 'llncs.cls'))

        latex = self.to_latex()

        with open(os.path.join(cwd, 'abstract.tex'), 'wb') as f:
            f.write(latex.encode('utf-8'))

        cmd = ['pdflatex', '-halt-on-error', 'abstract.tex']
        pipe = subprocess.PIPE

        for i in xrange(3):
            proc = subprocess.Popen(cmd, cwd=cwd, stdout=pipe, stderr=pipe)
            output, errors = proc.communicate()

            if proc.returncode:
                break

        return proc.returncode == 0
