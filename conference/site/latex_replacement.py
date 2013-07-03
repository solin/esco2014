import re

def latex_replacement(string_to_modify):

    string_to_latex = re.sub(r'\\?\&', r'\\&', string_to_modify)
    string_to_latex = re.sub(r'\\?\#', r'\\#', string_to_latex)
    string_to_latex = re.sub(r'\\?\%', r'\\%', string_to_latex)
    string_to_latex = re.sub(r'\\?\_', r'\\_', string_to_latex)

    return string_to_latex
