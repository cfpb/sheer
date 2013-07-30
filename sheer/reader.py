import re
import yaml
import codecs
import datetime
import os.path

FRONTMATTER = re.compile(r'^\s*---(.*)---\s*$', flags=re.MULTILINE | re.S)


def extract_frontmatter(data):
    match = FRONTMATTER.match(data)
    if match:
        return match.groups(1)[0], data[match.end():]

    return None, data


def json_safe_dates(document):
    for key in document.keys():
        if type(document[key]) == datetime.datetime:
            document[key] = document[key].strftime('%Y-%m-%dT%H:%M:00')
    return document


def annotations_from_filename(name):
    date_pattern = "%Y-%m-%d"
    date_string, remainder = name[:10], name[11:]
    try:
        values = {
            'date': datetime.datetime.strptime(date_string, date_pattern),
            '_id': remainder}
    except ValueError:
        values = {}
    return values


def document_from_str(data):
    frontmatter, text = extract_frontmatter(data)
    if frontmatter:
        document = yaml.load(frontmatter)
        document['text'] = text

    else:
        document = {'text': data}

    return document


def document_from_path(path):
    name = os.path.basename(path)
    with codecs.open(path, 'r', 'utf-8') as docfile:
        document = annotations_from_filename(name)
        document.update(document_from_str(docfile.read()))
        document = json_safe_dates(document)
        return document
