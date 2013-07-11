import re
import yaml
import codecs
import datetime

FRONTMATTER = re.compile(r'^\s*---(.*)---\s*$', flags=re.MULTILINE|re.S)


def extract_frontmatter(data):
    match = FRONTMATTER.match(data)
    if match:
        return match.groups(1)[0], data[match.end():]

    return None, data


def document_from_str(data):
    frontmatter, text = extract_frontmatter(data)
    if frontmatter:
        document= yaml.load(frontmatter)
        document['text'] = text

    else:
        document= {'text': data}
    for key in document.keys():
        if type(document[key]) == datetime.datetime:
            document[key] = document[key].strftime('%Y-%m-%dT%H:%M:00')

    return document


def document_from_path(path):
    with codecs.open(path, 'r','utf-8') as docfile:
        return document_from_str(docfile.read())
