import templates
import os
import os.path

from sheer import reader, exceptions


def render_html(physical_path, environment, context, request):
    markdown_path = physical_path[:-5] + '.md'
    markdown_exists = os.path.exists(markdown_path)

    # set up context
    context['request'] = request

    if markdown_exists:
        context.update(reader.document_from_path(markdown_path))

    # set up template
    if os.path.exists(physical_path):
        templatefile = file(physical_path)
        template = environment.from_string(templatefile.read())

    elif markdown_exists:
        if 'layout' in context:
            template_name = context['layout'] + '.html'
        else:
            template_name = "single.html"

        template = environment.get_template(template_name)

    else:
        raise exceptions.NoSuitableSourceFile()

    return template.render(**context)
