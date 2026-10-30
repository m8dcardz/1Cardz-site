#!/usr/bin/env python3
"""Turn the standalone index.html (doctype/head/body) into the fragment the claude.ai Artifact preview expects.
Usage: python3 tools/to_fragment.py index.html preview.html"""
import sys
src = open(sys.argv[1]).read()
vp = '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
if src.lstrip().lower().startswith('<!doctype'):
    src = src[src.index(vp) + len(vp):]
    src = src.replace('</style>\n</head>\n<body>', '</style>', 1)
    src = src.rstrip()
    for tail in ('</html>', '</body>'):
        if src.endswith(tail): src = src[:-len(tail)].rstrip()
open(sys.argv[2], 'w').write(src + '\n')
print('fragment', len(src), 'bytes')
