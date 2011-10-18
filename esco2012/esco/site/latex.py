class Latexible(object):

    def __unicode__(self):
        return self.to_latex()

    def to_latex(self):
        raise NotImplementedError

class Author(Latexible):

    _template = u"""\
{\\large %(person)s}\\\\
%(address)s\\\\
{\\tt %(email)s}
"""
    _presenting_person = u"\\underline{%(prefix)s %(first_name)s %(last_name)s}"
    _nonpresenting_person = u"%(prefix)s %(first_name)s %(last_name)s"

    def __init__(self, prefix, first_name, last_name, address, email, presenting):
        self.prefix = prefix
        self.first_name = first_name
        self.last_name = last_name
        self.address = address
        self.email = email
        self.presenting = presenting

    def to_latex(self):
        if self.presenting:
            person_template = self._presenting_person
        else:
            person_template = self._nonpresenting_person

        person = person_template % dict(
            prefix=self.prefix,
            first_name=self.first_name,
            last_name=self.last_name)

        return self._template % dict(
            person=person,
            address=self.address,
            email=self.email)

    @classmethod
    def from_json(cls, data):
        prefix = data['prefix']
        first_name = data['first_name']
        last_name = data['last_name']
        address = data['address']
        email = data['email']
        presenting = data['presenting']
        return cls(prefix, first_name, last_name, address, email, presenting)

class Authors(Latexible):

    _template = u"\\\\ \\vspace{4mm}"

    def __init__(self, *authors):
        self.authors = authors

    def to_latex(self):
        return self._template.join([ author.to_latex() for author in self.authors ])

    @classmethod
    def from_json(cls, data):
        return cls(*[ Author.from_json(author) for author in data ])

class BibAuthor(Latexible):

    _template = u"%(name_initial)s.~%(last_name)s"

    def __init__(self, name_initial, last_name):
        self.name_initial = name_initial
        self.last_name = last_name

    def to_latex(self):
        return self._template % dict(
            name_initial=self.name_initial,
            last_name=self.last_name)

    @classmethod
    def from_json(cls, data):
        name_initial = data['name_initial']
        last_name = data['last_name']
        return cls(name_initial, last_name)

class BibAuthors(Latexible):

    _template = u" and "

    def __init__(self, *authors):
        self.authors = authors

    def to_latex(self):
        return self._template.join([ author.to_latex() for author in self.authors ])

    @classmethod
    def from_json(cls, data):
        return cls(*[ BibAuthors.from_json(author) for author in data ])

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
\\author{} \\institute{}
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
        self.title = title
        self.authors = authors
        self.abstract = abstract
        self.bibitems = bibitems

    def to_latex(self):
        return self._template % dict(
            title=self.title,
            authors=self.authors.to_latex(),
            abstract=self.abstract,
            bibitems=self.bibitems.to_latex())

    @classmethod
    def from_json(cls, data):
        title = data['title']
        authors = Authors.from_json(data['authors'])
        abstract = data['abstract']
        bibitems = BibItems.from_json(data['bibitems'])
        return cls(title, authors, abstract, bibitems)
