from fanstatic import Library, Resource

library = Library('json', 'resources')

cycle = Resource(library, 'cycle.js', minified='cycle.min.js')

json = Resource(library, 'json.js', minified='json.min.js')

json2 = Resource(library, 'json2.js', minified='json2.min.js')

json_parse = Resource(library, 'json_parse.js', minified='json_parse.min.js')

json_parse_state = Resource(library,
    'json_parse_state.js', minified='json_parse_state.min.js')
