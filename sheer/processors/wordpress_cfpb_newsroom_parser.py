from wordpress_json_api import read_url

def documents(name, url):
    # import pdb;pdb.set_trace()
    results = read_url(url)
    return process_data(results)

def process_data(data):
    for ndx, value in enumerate(data):
        value['_id'] = value['slug']
        # remove fields we're not interested in
        for cat in value['categories']:
            del cat['id']
        for item in value['taxonomy_cfpb_newsroom_tag_taxonomy']:
            del item['id']
        for item in value['taxonomy_cfpb_newsroom_cat_taxonomy']:
            del item['id']
        del value['author']['id']
        del value['id']
        data[ndx] = value
    return data
