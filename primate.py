REPLACEMENTS = list()
def configure(options):
    for search, replace in options.items():
        REPLACEMENTS.append((search, replace))

def transform_privmsg(message):
    for search, replace in REPLACEMENTS:
        message = message.replace(search, replace)
    return message
