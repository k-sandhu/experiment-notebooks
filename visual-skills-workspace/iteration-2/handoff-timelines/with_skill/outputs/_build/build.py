import pathlib
h = pathlib.Path(__file__).parent
base = (h / 'base.html').read_text(encoding='utf-8')
cut = base.index('/* ===== SCENE')
tail = '</script>\n</body></html>\n'
out = base[:cut] + (h / 'data.js').read_text(encoding='utf-8') + '\n' + (h / 'scene.js').read_text(encoding='utf-8') + tail
out = out.replace('<title>Handoff replay</title>', '<title>Handoff timing replay</title>')
(h.parent / 'explainer.html').write_text(out, encoding='utf-8')
print(len(out))
