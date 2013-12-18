import templates
import os
import os.path
import codecs
import json

import elasticsearch

from sheer import reader, exceptions


def render_html(physical_path, environment, context, request):
    markdown_path = physical_path[:-5] + '.md'
    markdown_exists = os.path.exists(markdown_path)

    physical_directory, filename = os.path.split(physical_path)
    lookup, _ = os.path.splitext(filename)

    lookup_json_path= os.path.join(physical_directory, '_lookup.json')

    # set up context
    context['request'] = request

    if markdown_exists:
        context.update(reader.document_from_path(markdown_path))

    # set up template
    if os.path.exists(physical_path):
        templatefile = codecs.open(physical_path, "r", "utf-8")
        template = environment.from_string(templatefile.read())

    elif markdown_exists:
        if 'layout' in context:
            template_name = context['layout'] + '.html'
        else:
            template_name = "single.html"

        template = environment.get_template(template_name)

    elif os.path.exists(lookup_json_path):
        es = elasticsearch.Elasticsearch() # TODO: this is stupid, should pull from site
        lookup_file = codecs.open(lookup_json_path, encoding='utf8')
        lookups = json.loads(lookup_file.read())
        for lookup_option in lookups:
            document = es.get_source(index="content", id=lookup, doc_type=lookup_option)
            if document:
                context.update(document)
                if 'layout' in context:
                    template_name = context['layout'] + '.html'
                else:
                    template_name = "single.html"

                template = environment.get_template(template_name)
                break
    else:
        raise exceptions.NoSuitableSourceFile()

    return template.render(**context)
