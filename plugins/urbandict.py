import urllib.request
import json


@yui.command('ud', 'urban', 'urbandict')
def ud(argv):
    if len(argv) < 2:
        return

    word = argv[1]
    definition = None
    idx = 0

    try:
        if len(argv) > 2:
            idx = int(argv[2]) - 1
        url = 'http://api.urbandictionary.com/v0/define?term=%s' % urllib.request.quote(word.encode('utf-8'))
        resp = urllib.request.urlopen(url)
        # get encoding
        enc = resp.headers['content-type'].split('charset=')[-1]
        content = resp.read().decode(enc)
        js = json.loads(content)
        definition = js['list'][idx]['definition']
    except Exception as ex:
        print(ex)

    if not definition:
        return 'No results for "%s" :(' % word
    else:
        return '"%s": %s' % (word, definition)
