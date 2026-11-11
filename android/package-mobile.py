"""Prepare Android assets from the repository's single-file mobile studio."""
from pathlib import Path
here = Path(__file__).resolve().parent
source = here.parent / 'studio-mobile.html'
out = here / 'build/assets/studio-mobile.html'
out.parent.mkdir(parents=True, exist_ok=True)
html = source.read_text(encoding='utf-8')
script = (here / 'mobile.js').read_text(encoding='utf-8')
out.write_text(html.replace('</html>', '<script>\n' + script + '\n</script></html>'), encoding='utf-8')
