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
    %(address)s\\\\
    """

##---
#    _presenting_person = u"{\\bf %(full_name)s}\\\\"
#    _nonpresenting_person = u"{\\bf %(full_name)s}\\\\"
    _presenting_person = u"{\\bf %(first_name)s %(last_name)s}\\\\"
    _nonpresenting_person = u"{\\bf %(first_name)s %(last_name)s}\\\\"
##***

##---
#    def __init__(self, full_name, affiliation, email, presenting):
#        self.full_name = full_name.strip()
#        self.affiliation = affiliation.strip()
#        self.email = email
#        self.presenting = presenting

    def __init__(self, first_name, last_name, address, email, presenting):
        self.first_name = first_name.strip()
        self.last_name = last_name.strip()
        self.address = address.strip()
        self.email = email
        self.presenting = presenting
##***


    def to_latex(self, single_author=False):
        if not single_author and self.presenting == 'yes':
            person_template = self._presenting_person
        else:
            person_template = self._nonpresenting_person

##---
#        person = person_template % dict(
#            full_name = self.full_name)
#
#        return self._template % dict(
#            person = person,
#            affiliation = self.affiliation,
#            email = self.email)

        person = person_template % dict(
            first_name = self.first_name,
            last_name = self.last_name)

        return self._template % dict(
            person = person,
            address = self.address,
            email = self.email)
##***

    @classmethod
    def from_json(cls, data):
##---
#        full_name = data.get('full_name', "")
#        affiliation = data.get('affiliation', "")
#        email = data.get('email', "")
#        presenting = data['presenting']
#        return cls(full_name, affiliation, email, presenting)

        first_name = data.get('first_name', "")
        last_name = data.get('last_name', "")
        address = data.get('address', "")
        email = data.get('email', "")
        presenting = data['presenting']
        return cls(first_name, last_name, address, email, presenting)
##***


class TocAuthor(Latexible):

    _template = u"%(person)s"

##---
#    _presenting_person = u"%(full_name)s"
#    _nonpresenting_person = u"%(full_name)s"
    _presenting_person = u"%(first_name)s %(last_name)s"
    _nonpresenting_person = u"%(first_name)s %(last_name)s"
##***

##---
#    def __init__(self, full_name, affiliation, email, presenting):
#        self.full_name = full_name
#        self.affiliation = affiliation
#        self.email = email
#        self.presenting = presenting

    def __init__(self, first_name, last_name, address, email, presenting):
        self.first_name = first_name
        self.last_name = last_name
        self.address = address
        self.email = email
        self.presenting = presenting
##***

    def to_latex(self, single_author=False):
        if not single_author and self.presenting == 'yes':
            person_template = self._presenting_person
        else:
            person_template = self._nonpresenting_person

##---
#        person = person_template % dict(
#            full_name = self.full_name)
#
#        return self._template % dict(
#            person = person,
#            affiliation = self.affiliation,
#            email = self.email)

        person = person_template % dict(
            first_name = self.first_name,
            last_name = self.last_name)

        return self._template % dict(
            person = person,
            address = self.address,
            email = self.email)
##***

    @classmethod
    def from_json(cls, data):
##---
#        full_name = data.get('full_name', "")
#        affiliation = data.get('affiliation', "")
#        email = data.get('email', "")
#        presenting = data['presenting']
#        return cls(full_name, affiliation, email, presenting)

        first_name = data.get('first_name', "")
        last_name = data.get('last_name', "")
        address = data.get('address', "")
        email = data.get('email', "")
        presenting = data['presenting']
        return cls(first_name, last_name, address, email, presenting)
##***

class Author(Latexible):

    _template = u"""\
{\\large %(person)s}\\\\
%(address)s\\\\
{\\tt %(email)s}"""

##---
#    _presenting_person = u"\\underline{%(full_name)s}"
#    _nonpresenting_person = u"%(full_name)s"
    _presenting_person = u"\\underline{%(first_name)s %(last_name)s}"
    _nonpresenting_person = u"%(first_name)s %(last_name)s"
##***

##---
#    def __init__(self, full_name, affiliation, email, presenting):
#        self.full_name = full_name
#        self.affiliation = affiliation
#        self.email = email
#        self.email = email.replace('_', '\_')
#        self.presenting = presenting

    def __init__(self, first_name, last_name, address, email, presenting):
        self.first_name = first_name
        self.last_name = last_name
        self.address = address
        self.email = email
        self.email = email.replace('_', '\_')
        self.presenting = presenting
##***

    def to_latex(self, single_author=False):
        if not single_author and self.presenting == 'yes':
            person_template = self._presenting_person
        else:
            person_template = self._nonpresenting_person
##---
#        person = person_template % dict(
#            full_name = self.full_name)
#
#        return self._template % dict(
#            person = person,
#            affiliation = self.affiliation,
#            email = self.email)

        person = person_template % dict(
            first_name = self.first_name,
            last_name = self.last_name)

        return self._template % dict(
            person = person,
            address = self.address,
            email = self.email)
##***

    @classmethod
    def from_json(cls, data):
##---
#        full_name = data.get('full_name', "")
#        affiliation = data.get('affiliation', "")
#        email = data.get('email', "")
#        presenting = data['presenting']
#        return cls(full_name, affiliation, email, presenting)

        #first_name = data.get('first_name', "")
        first_name = data['first_name']
        last_name = data.get('last_name', "")
        address = data.get('address', "")
        email = data.get('email', "")
        presenting = data['presenting']
        return cls(first_name, last_name, address, email, presenting)
##***

class Authors(Latexible):

    _template = u"\n\\\\ \\vspace{4mm}\n"

    def __init__(self, *authors):
        self.authors = authors

    def to_latex(self):
        single_author = len(self.authors) == 1
        return self._template.join([author.to_latex(single_author) for author in self.authors])

    @classmethod
    def from_json(cls, data):
        return cls(*[Author.from_json(author) for author in data ])

##--- code for groups of authors of same institution on abstract
#class AuthAuthor(Latexible):
#
#    _template = u"{\\large %(auth_person)s}"
#
#    _presenting_person = u"\\underline{%(auth_full_name)s}"
#    _nonpresenting_person = u"%(auth_full_name)s"
#
#    def __init__(self, auth_full_name, auth_presenting):
#        self.auth_full_name = auth_full_name
#        self.auth_presenting = auth_presenting
#
#    def to_latex(self, single_author=False):
#        if not single_author and self.auth_presenting == 'yes':
#            person_template = self._presenting_person
#        else:
#            person_template = self._nonpresenting_person
#
#        auth_person = person_template % dict(
#            auth_full_name = self.auth_full_name)
#
#        return self._template % dict(
#            auth_person = auth_person)
#
#    @classmethod
#    def from_json(cls, data):
#        auth_full_name = data['auth_full_name']
#        auth_presenting = data['auth_presenting']
#        return cls(auth_full_name, auth_presenting)
#
#class AuthAuthors(Latexible):
#
#    _template = u", "
#
#    def __init__(self, *auth_authors):
#        self.auth_authors = auth_authors
#
#    def to_latex(self):
#        single_author = len(self.auth_authors) == 1
#        return self._template.join([auth_author.to_latex(single_author) for auth_author in self.auth_authors])
#
#    @classmethod
#    def from_json(cls, data):
#       return cls(*[AuthAuthor.from_json(auth_author) for auth_author in data])
#
#class AuthEmail(Latexible):
#
#    _template = u"%(auth_email)s"
#
#    def __init__(self, auth_email):
#        self.auth_email = auth_email
#        self.auth_email = auth_email.replace('_', '\_')
#
#    def to_latex(self):
#        return self._template % dict(
#            auth_email = self.auth_email)
#
#    @classmethod
#    def from_json(cls, data):
#        auth_email = data['auth_email']
#        return cls(auth_email)
#
#class AuthEmails(Latexible):
#
#    _template = u", "
#
#    def __init__(self, *auth_emails):
#        self.auth_emails = auth_emails
#
#    def to_latex(self):
#        return self._template.join([auth_email.to_latex() for auth_email in self.auth_emails ])
#
#    @classmethod
#    def from_json(cls, data):
#       return cls(*[AuthEmail.from_json(auth_email) for auth_email in data ])
#
#class AuthGroup(Latexible):
#
#    _template = u"""\
#{%(authgroup_authors)s}\\\\
#%(authgroup_affiliation)s\\\\
#{\\tt %(authgroup_emails)s}"""
#
#    def __init__(self, authgroup_authors, authgroup_affiliation, authgroup_emails):
#        self.authgroup_authors = authgroup_authors
#	self.authgroup_affiliation = authgroup_affiliation
#        self.authgroup_emails = authgroup_emails
#
#    def to_latex(self):
#        return self._template % dict(
#            authgroup_authors = self.authgroup_authors.to_latex(),
#            authgroup_affiliation = self.authgroup_affiliation,
#            authgroup_emails = self.authgroup_emails.to_latex())
#
#    @classmethod
#    def from_json(cls, data):
#        authgroup_authors = AuthAuthors.from_json(data['authgroup_authors'])
#        authgroup_affiliation = data['authgroup_affiliation']
#        authgroup_emails = AuthEmails.from_json(data['authgroup_authors'])
#        return cls(authgroup_authors, authgroup_affiliation, authgroup_emails)
#
#class AuthGroups(Latexible):
#
#    _template = u"\n\\\\ \\vspace{4mm}\n"
#
#    def __init__(self, *authorgroups):
#        self.authorgroups = authorgroups
#
#    def to_latex(self):
#        return self._template.join([authorgroup.to_latex() for authorgroup in self.authorgroups])
#
#    @classmethod
#    def from_json(cls, data):
#        return cls(*[AuthGroup.from_json(authorgroup) for authorgroup in data ])
##***

class BibAuthor(Latexible):

##--
#    _template = u"%(bibauthor_first_name)s %(bibauthor_last_name)s"
#
#    def __init__(self, bibauthor_first_name, bibauthor_last_name):
#        self.bibauthor_first_name = bibauthor_first_name
#        self.bibauthor_last_name = bibauthor_last_name
#
#    def to_latex(self):
#        return self._template % dict(
#            bibauthor_first_name = self.bibauthor_first_name,
#            bibauthor_last_name = self.bibauthor_last_name)
#
#    @classmethod
#    def from_json(cls, data):
#        bibauthor_first_name = data['bibauthor_first_name']
#        try:
#            bibauthor_last_name = data['bibauthor_last_name']
#        except KeyError:
#            bibauthor_last_name = ""
#        return cls(bibauthor_first_name, bibauthor_last_name)

    _template = u"%(first_name)s %(last_name)s"

    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name

    def to_latex(self):
        return self._template % dict(
            first_name = self.first_name,
            last_name = self.last_name)

    @classmethod
    def from_json(cls, data):
        first_name = data['first_name']
        try:
            last_name = data['last_name']
        except KeyError:
            last_name = ""
        return cls(first_name, last_name)
##***

class BibAuthors(Latexible):

    _template = u" and "

##--
#    def __init__(self, *bibauthors):
#        self.bibauthors = bibauthors
#
#    def to_latex(self):
#        return self._template.join([bibauthor.to_latex() for bibauthor in self.bibauthors])
#
#    @classmethod
#    def from_json(cls, data):
#       return cls(*[BibAuthor.from_json(bibauthor) for bibauthor in data])

    def __init__(self, *authors):
        self.authors = authors

    def to_latex(self):
        return self._template.join([author.to_latex() for author in self.authors])

    @classmethod
    def from_json(cls, data):
       return cls(*[BibAuthor.from_json(author) for author in data])
##***

class BibItem(Latexible):

    _template = u"""\
\\bibitem{%(bibid)s}
{\\sc %(authors)s}. {%(title)s}. %(other)s."""

##---
#    def __init__(self, bibid, bibauthors, bibtitle, bibother):
#        self.bibid = bibid
#        self.bibid = "".join([x for x in self.bibid if ord(x) < 128])
#        self.bibauthors = bibauthors
#        self.bibtitle = bibtitle.replace('&quot;', '')
#	 self.bibother = bibother
    def __init__(self, bibid, authors, title, other):
        self.bibid = bibid
        self.bibid = "".join([x for x in self.bibid if ord(x) < 128])
        self.authors = authors
        self.title = title.replace('&quot;', '')
	self.other = other
##***

    def to_latex(self):
        return self._template % dict(
            bibid = self.bibid,
##---
#            bibauthors = self.bibauthors.to_latex(),
#            bibtitle = self.bibtitle,
#            bibother = self.bibother)
            authors = self.authors.to_latex(),
            title = self.title,
            other = self.other)
##***

    @classmethod
    def from_json(cls, data):
##---
#        bibid = data['bibitem_title']
#        bibauthors = BibAuthors.from_json(data['bibitem_authors'])
#        bibtitle = data['bibitem_title']
#        bibother = data['bibitem_other']
#        return cls(bibid, bibauthors, bibtitle, bibother)
        bibid = data['title']
        authors = BibAuthors.from_json(data['authors'])
        title = data['title']
        other = data['other']
        return cls(bibid, authors, title, other)
##***

class BibItems(Latexible):

    _template = u"\n\n"

    def __init__(self, *bibitems):
        self.bibitems = bibitems

    def to_latex(self):
        return self._template.join([bibitem.to_latex() for bibitem in self.bibitems])

    @classmethod
    def from_json(cls, data):
        return cls(*[BibItem.from_json(bibitem) for bibitem in data])

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

\\section*{Abstract}

%(abstract)s

\\bibliographystyle{plain}
\\begin{thebibliography}{10}
%(bibitems)s
\\end{thebibliography}

\\end{document}
"""

##---
#    def __init__(self, title, abstract, authors, authorgroups, bibitems):
    def __init__(self, title, abstract, authors, bibitems):
##***
        self.title = title.replace('\n', '').replace('\r', '').replace('&quot;', '')
        self.title = self.title.replace('"', '')
        self.title = self.title.replace('%', '\%')
        self.title = self.title.replace('&', '\&')
        self.title = self.title.replace('#', '\#')
        self.title = self.title.replace('$hp$', 'hp')
        self.title = self.title.strip()
        self.abstract = abstract.replace('\n', '').replace('\r', '')
        self.abstract = self.abstract.replace('%', '\%')
        self.abstract = self.abstract.replace('&', '\&')
        self.abstract = self.abstract.replace('#', '\#')
        self.authors = authors
##---
#        self.authorgroups = authorgroups
##***
        self.bibitems = bibitems
        toc_author = []
        temp_presenting = {}

##---
#        for author in self.authors.authors:
#            temp_presenting[author.full_name]=PresentingAuthor(author.full_name, author.affiliation, author.email, author.presenting)
#            if author.presenting == 'yes':
#                toc_author.append(TocAuthor(author.full_name, author.affiliation, author.email, author.presenting))
#            elif len(toc_author) == 0:
#                toc_author.append(TocAuthor(author.full_name, author.affiliation, author.email, author.presenting))
        for author in self.authors.authors:          
            temp_presenting[author.last_name + " " + author.first_name]=PresentingAuthor(author.first_name, author.last_name, author.address, author.email, author.presenting)
            if author.presenting == 'yes':
                toc_author.append(TocAuthor(author.first_name, author.last_name, author.address, author.email, author.presenting))
            elif len(toc_author) == 0:
                toc_author.append(TocAuthor(author.first_name, author.last_name, author.address, author.email, author.presenting))
##***

        self.presenting = PresentingAuthors(temp_presenting)
        self.tocauthors = TocAuthors(toc_author)

    def to_latex(self):
        return self._template % dict(
            title = self.title,
            authors = self.authors.to_latex(),
##---
#            authorgroups = self.authorgroups.to_latex(),
##***
            tocauthors = self.tocauthors.to_latex(),
            abstract = self.abstract,
            bibitems = self.bibitems.to_latex())

    def to_latex_raw(self):
        return self._template_abstracts % dict(
            title = self.title,
            authors = self.authors.to_latex(),
##---
#            authorgroups = self.authorgroups.to_latex(),
##***
            tocauthors = self.tocauthors.to_latex(),
            abstract = self.abstract,
            bibitems = self.bibitems.to_latex())

    def to_latex_presenting(self):
        return self._template_presenting % dict(authors = self.presenting)

    @classmethod
    def from_json(cls, data):
        title = titlecase(data['title'])
        abstract = data['abstract']
        authors = Authors.from_json(data['authors'])
##---
#        authorgroups = AuthGroups.from_json(data['authgroups'])
#        bibitems = BibItems.from_json(data['bibitems'])
#        return cls(title, abstract, authors, authorgroups, bibitems)
        bibitems = BibItems.from_json(data['bibitems'])
        return cls(title, abstract, authors, bibitems)
##***

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
