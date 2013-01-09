from __future__ import with_statement

import os
import re
import string
import shutil
import subprocess

from femtec.settings import MEDIA_ROOT
from titlecase import titlecase

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

    _template = u""

    def __init__(self, authors):
        self.authors = authors

    def to_latex(self):
        single_author = len(self.authors) == 1
        return self._template.join([ author.to_latex(single_author) for author in self.authors ])


class PresentingAuthors(Latexible):

    _template = u""

    def __init__(self, authors):
        self.authors = authors
        self.sorted_keys = authors.keys()
        self.sorted_keys.sort()


    def to_latex(self):
        single_author = len(self.authors) == 1
        #return self._template.join([ author.to_latex(single_author) for author in self.authors ])
        strlist = []
        for key in self.sorted_keys:
            strlist.append(self.authors[key].to_latex(single_author))
        return self._template.join(strlist)

class PresentingAuthor(Latexible):

    _template = u"""\
    \\noindent
    %(person)s
    %(affiliation)s\\\\
    """
    _presenting_person = u"{\\bf %(full_name)s}\\\\"
    _nonpresenting_person = u"{\\bf %(full_name)s}\\\\"

    def __init__(self, full_name, affiliation, email, presenting):
        self.full_name = full_name.strip()
        self.affiliation = affiliation.strip()
        self.email = email
        self.presenting = presenting

    def to_latex(self, single_author=False):
        if not single_author and self.presenting == 'yes':
            person_template = self._presenting_person
        else:
            person_template = self._nonpresenting_person

        person = person_template % dict(
            full_name=self.full_name)

        return self._template % dict(
            person=person,
            affiliation=self.affiliation,
            email=self.email)

    @classmethod
    def from_json(cls, data):
        full_name = data.get('full_name', "")
        affiliation = data.get('affiliation', "")
        email = data.get('email', "")
        presenting = data['presenting']
        return cls(full_name, affiliation, email, presenting)


class TocAuthor(Latexible):

    _template = u"%(person)s"
    _presenting_person = u"%(full_name)s"
    _nonpresenting_person = u"%(full_name)s"

    def __init__(self, full_name, affiliation, email, presenting):
        self.full_name = full_name
        self.affiliation = affiliation
        self.email = email
        self.presenting = presenting

    def to_latex(self, single_author=False):
        if not single_author and self.presenting == 'yes':
            person_template = self._presenting_person
        else:
            person_template = self._nonpresenting_person

        person = person_template % dict(
            full_name=self.full_name)

        return self._template % dict(
            person=person,
            affiliation=self.affiliation,
            email=self.email)

    @classmethod
    def from_json(cls, data):
        full_name = data.get('full_name', "")
        affiliation = data.get('affiliation', "")
        email = data.get('email', "")
        presenting = data['presenting']
        return cls(full_name, affiliation, email, presenting)


class Author(Latexible):

    _template = u"""\
{\\large %(person)s}\\\\
%(affiliation)s\\\\
{\\tt %(email)s}"""

    _presenting_person = u"\\underline{%(full_name)s}"
    _nonpresenting_person = u"%(full_name)s"

    def __init__(self, full_name, affiliation, email, presenting):
        self.full_name = full_name
        self.affiliation = affiliation
        self.email = email.replace('_', '\_')
        self.presenting = presenting

    def to_latex(self, single_author=False):
        if not single_author and self.presenting == 'yes':
            person_template = self._presenting_person
        else:
            person_template = self._nonpresenting_person

        person = person_template % dict(
            full_name=self.full_name)

        return self._template % dict(
            person=person,
            affiliation=self.affiliation,
            email=self.email)

    @classmethod
    def from_json(cls, data):
        full_name = data.get('full_name', "")
        affiliation = data.get('affiliation', "")
        email = data.get('email', "")
        presenting = data['presenting']
        return cls(full_name, affiliation, email, presenting)

class Authors(Latexible):

    _template = u"\n\\\\ \\vspace{4mm}\n"

    def __init__(self, *authors):
        self.authors = authors

    def to_latex(self):
        single_author = len(self.authors) == 1
        return self._template.join([author.to_latex(single_author) for author in self.authors])

    @classmethod
    def from_json(cls, data):
        return cls(*[ Author.from_json(author) for author in data ])
###
class gAuthor(Latexible):

    _template = u"%(gfull_name)s "

    def __init__(self, gfull_name):
        self.gfull_name = gfull_name

    def to_latex(self):
        return self._template % dict(
            gfull_name=self.gfull_name)

    @classmethod
    def from_json(cls, data):
        gfull_name = data['gfull_name']
        return cls(gfull_name)

class gAuthors(Latexible):

    _template = u" and "

    def __init__(self, *gauthors):
        self.gauthors = gauthors

    def to_latex(self):
        return self._template.join([ gauthor.to_latex() for gauthor in self.gauthors ])

    @classmethod
    def from_json(cls, data):
       return cls(*[ gAuthor.from_json(gauthor) for gauthor in data ])

class gItem(Latexible):

    _template = u"""\
{\\sc %(gauthors)s}. {%(gaffiliation)s}.."""

    def __init__(self, gauthors, gaffiliation):
        self.gauthors = gauthors
	self.gaffiliation = gaffiliation

    def to_latex(self):
        return self._template % dict(
            gauthors=self.gauthors.to_latex(),
            gaffiliation=self.gaffiliation)

    @classmethod
    def from_json(cls, data):
        gauthors = gAuthors.from_json(data['gauthor'])
        gaffiliation = data['gaffiliation']
        return cls(gauthors, gaffiliation)

class gItems(Latexible):

    _template = u"\n\n"

    def __init__(self, *gitems):
        self.gitems = gitems

    def to_latex(self):
        return self._template.join([gitem.to_latex() for gitem in self.gitems])

    @classmethod
    def from_json(cls, data):
        return cls(*[ gItem.from_json(gitem) for gitem in data ])
###
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

    _template = u"""\
\\bibitem{%(bibid)s}
{\\sc %(bibauthors)s}. {%(bibtitle)s}. %(bibother)s."""

    def __init__(self, bibid, bibauthors, bibtitle, bibother):
        self.bibid = bibid
        self.bibid = "".join([x for x in self.bibid if ord(x) < 128])
        self.bibauthors = bibauthors
        self.bibtitle = bibtitle.replace('&quot;', '')
	self.bibother = bibother

    def to_latex(self):
        return self._template % dict(
            bibid=self.bibid,
            bibauthors=self.bibauthors.to_latex(),
            bibtitle=self.bibtitle,
            bibother=self.bibother)

    @classmethod
    def from_json(cls, data):
        bibid = data['bibitem_title']
        bibauthors = BibAuthors.from_json(data['bibitem_authors'])
        bibtitle = data['bibitem_title']
        bibother = data['bibitem_other']
        return cls(bibid, bibauthors, bibtitle, bibother)

class BibItems(Latexible):

    _template = u"\n\n"

    def __init__(self, *bibitems):
        self.bibitems = bibitems

    def to_latex(self):
        return self._template.join([bibitem.to_latex() for bibitem in self.bibitems])

    @classmethod
    def from_json(cls, data):
        return cls(*[ BibItem.from_json(bibitem) for bibitem in data ])


class Abstract(Latexible):

    _template_abstracts = u"""\
\\title{%(title)s}
\\tocauthor{%(tocauthors)s} \\author{} \\institute{}
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

"""

    _template_presenting = u"%(authors)s"

    _template = u"""\
\\documentclass[article,A4,11pt]{llncs}
\\usepackage[utf8]{inputenc}
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
\\author{} 
\\tocauthor{%(tocauthors)s} 
\\institute{}
\\maketitle

\\begin{center}
%(authors)s
\end{center}

%(gitems)s

\\section*{Abstract}

%(abstract)s

\\bibliographystyle{plain}
\\begin{thebibliography}{10}
%(bibitems)s
\\end{thebibliography}

\\end{document}
"""

    def __init__(self, title, authors, abstract, bibitems, gitems):
        self.title = title.replace('\n', '').replace('\r', '').replace('&quot;', '')
        self.title = self.title.replace('"', '')
        self.title = self.title.replace('%', '\%')
        self.title = self.title.replace('&', '\&')
        self.title = self.title.replace('#', '\#')
        self.title = self.title.replace('$hp$', 'hp')
        #self.title = "".join([x for x in self.title if ord(x) < 128])
        self.title = self.title.strip()
        self.authors = authors
        self.abstract = abstract.replace('\n', '').replace('\r', '')
        self.abstract = self.abstract.replace('%', '\%')
        self.abstract = self.abstract.replace('&', '\&')
        self.abstract = self.abstract.replace('#', '\#')
        self.bibitems = bibitems
        self.gitems = gitems
        toc_author = []
        temp_presenting = {}
        for author in self.authors.authors:
            temp_presenting[author.full_name]=PresentingAuthor(author.full_name, author.affiliation, author.email, author.presenting)
            if author.presenting == 'yes':
                toc_author.append(TocAuthor(author.full_name, author.affiliation, author.email, author.presenting))
            elif len(toc_author) == 0:
                toc_author.append(TocAuthor(author.full_name, author.affiliation, author.email, author.presenting))
        self.presenting = PresentingAuthors(temp_presenting)
        self.tocauthors = TocAuthors(toc_author)

    def to_latex(self):
        return self._template % dict(
            title=self.title,
            authors=self.authors.to_latex(),
            tocauthors=self.tocauthors.to_latex(),
            abstract=self.abstract,
            bibitems=self.bibitems.to_latex(),
            gitems=self.gitems.to_latex())

    def to_latex_raw(self):
        return self._template_abstracts % dict(
            title=self.title,
            authors=self.authors.to_latex(),
            tocauthors=self.tocauthors.to_latex(),
            abstract=self.abstract,
            bibitems=self.bibitems.to_latex(),
            gitems=self.gitems.to_latex())

    def to_latex_presenting(self):
        return self._template_presenting % dict(authors=self.presenting)

    @classmethod
    def from_json(cls, data):
        title = titlecase(data['title'])
        authors = Authors.from_json(data['authors'])
        abstract = data['abstract']
        bibitems = BibItems.from_json(data['bibitems'])
        gitems = gItems.from_json(data['gitems'])
        return cls(title, authors, abstract, bibitems, gitems)

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
