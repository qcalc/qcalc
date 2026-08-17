# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qutil import qdomain, qaddr, iif
from qsite import STATIC_VERSION
from django.templatetags.static import static
from django.utils.html import format_html


def get_html(title: str, desc: str, canonical: str = '',
             imagelist: list | None = None, csslist: list | None = None, categories: list | None = None):
    imagelist = iif(imagelist is None, [
        # Primary image for Open Graph
        _static_ver('qsite/images/logo-xh-1200x630.png'),
        # Fallback images for Open Graph
        _static_ver('qsite/images/logo-fb-1080x1080.png'),
    ], imagelist)
    img_tw = imagelist[0]
    img_fb = imagelist[0] if len(imagelist) == 1 else imagelist[1]
    csslist = iif(csslist is None, [], csslist)

    html = f'''
    <title>{title}</title>
    <meta name="description" content="{desc}" />
    <link rel="canonical" href="{qaddr()}{canonical}" />
    <meta property="og:site_name" content="{qdomain()}" />
    <meta property="og:type" content="article" />
    <meta property="og:title" content="{title}" />
    <meta property="og:description" content="{desc}" />
    <meta property="og:url" content="{qaddr()}{canonical}" />
    <meta property="og:image" content="{img_fb}" />
    <meta property="og:image:alt" content="Calculators for you - Measure, Calculate, Improve!" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{title}" />
    <meta name="twitter:image" content="{img_tw}" />
    <meta name="twitter:description" content="{desc}" />
    '''
    for css in csslist:
        html += f'''<link href="{css}" rel="stylesheet" type="text/css">
    '''
    html += get_ldjson(title, desc, canonical, categories)
    return html


def get_js(jslist: list | None = None):
    jslist = iif(jslist is None, [], jslist)
    html = ''
    for js in jslist:
        html += f'<script src="{js}" ></script>\n'
    return html


def get_ldjson(title: str, desc: str, canonical: str = '', categories: list | None = None):
    if canonical == '': return ''
    comma = iif(categories is not None, ',', '')
    ldjson = f"""<script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "WebPage",
      "name": "{title}",
      "description": "{desc}",
      "url": "{qaddr()}{canonical}"{comma}
      """

    if categories is not None and len(categories) > 0:
        ldjson += f""""breadcrumb": {{
      "@type": "BreadcrumbList",
      "itemListElement": [
        """
        i = 0
        for i, category in enumerate(categories):
            category = category.lower()
            ldjson += f"""{{
            "@type": "ListItem",
            "position": {i + 1},
            "name": "{category}",
            "item": "{qaddr()}/catalog/{category}/"
          }},
          """
        ldjson += f"""{{
            "@type": "ListItem",
            "position": {i + 2},
            "name": "{title}",
            "item": "{qaddr()}{canonical}"
          }}
        ]
      }},
      "mainEntity": {{
        "@type": "SoftwareApplication",
        "name": "{title}",
        "description": "{desc}",
        "applicationCategory": "{categories[-1]}",
        "operatingSystem": "Web",
        "url": "{qaddr()}{canonical}",
        "author": {{
          "@type": "Organization",
          "name": "{qdomain()}"
        }}
      }}
    """

    ldjson += f"""}}
    </script>
    """
    return ldjson


def _static_ver(path):
    full_url = f'{qaddr()}{static(path)}'
    return format_html(f'{full_url}?v={STATIC_VERSION}')


def _test():
    print(get_js())
    head = get_html('Hello', 'Hello World', csslist=['xyz.css', 'abc.css'])
    print(head)
    head = get_html('Hello', 'Hello World', '/page/about/')
    print(head)
    head = get_html('Hello', 'Hello World', '/calc/bmi/')
    print(head)
    head = get_html('Hello', 'Hello World', '/calc/bmi/', categories=['Health'])
    print(head)
    head = get_html('Hello', 'Hello World', '/calc/eoq/', categories=['Business', 'SCM'])
    print(head)


if __name__ == '__main__':
    _test()
