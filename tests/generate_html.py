from tornado import template

tpl_buf = open("diff_template.html").read()
out_html = open('diff1.html', 'w')

t = template.Template(tpl_buf)
diff_files = [ {
    'name': 'uc-code/uc-model/uc-model-v2/uc-collection-file-v2/src/main/resources/xsd/ls_file.xsd',
    'lines': [ {
            'type' : 'line',
            'left' : 'Line 1',
            'right': 'Line 1',
        }, {
            'type' : 'add',
            'left' : '',
            'right': 'Line two',
        }, {
            'type' : 'change',
            'left' : 'Line 3',
            'right': 'Line three',
        }, {
            'type' : 'dump',
            'left' : 'Line four',
            'right': 'Line four',
        }, {
            'type' : 'dump',
            'left' : 'Line 5',
            'right': 'Line 5',
        }, {
            'type': 'remove',
            'left': 'Line six',
            'right': '',
    } ]
} ]

out_html.write(t.generate(diff_files=diff_files))


