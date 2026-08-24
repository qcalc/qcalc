import json
from pathlib import Path
from qutil import TreeNode
from django.conf import settings
import posixpath
from urllib.parse import urlsplit, urlunsplit
from bs4 import BeautifulSoup
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

DOC_EXTENSIONS = {'.md', '.html', '.txt'}
DOCS_META_FILE = 'docs_meta.json'


def get_doc_path(doc_file):
    doc_path = Path(settings.DOCS_FILES_DIR) / doc_file
    return doc_path


# do not allow PROJ_DIR - unsafe
# def get_read_path(doc_file):
#     doc_path = Path(settings.PROJ_DIR) / doc_file
#     return doc_path

def _doc_title_from_name(name):
    return name.replace('_', ' ').replace('-', ' ').strip().title().replace('Qcalc','qCalc')


def _load_docs_meta(docs_root: Path) -> dict:
    # | sidecar JSON manifest overriding title/desc/tags/order/hidden per relative path, e.g.:
    meta_path = docs_root / DOCS_META_FILE
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f'!!! LDM: Could not read {meta_path}: {e}')
        return {}


def build_docs_tree(nid='docs', title='Documentation'):
    # | Builds a TreeNode tree mirroring settings.DOCS_FILES_DIR, with per-node
    # | title/desc/tags/order/hidden overridable via a docs_meta.json sidecar manifest.
    docs_root = Path(settings.DOCS_FILES_DIR)
    meta = _load_docs_meta(docs_root)

    root = TreeNode(nid=nid, name=nid, title=title, is_leaf=False, node_type='doc')
    root._index_node()

    def add_dir(node, dir_path, id_prefix):
        try:
            entries = sorted(dir_path.iterdir(), key=lambda p: p.name.lower())
        except OSError as e:
            logger.warning(f'!!! BDT: Could not list {dir_path}: {e}')
            return
        for entry in entries:
            if entry.name.startswith('.') or entry.name == DOCS_META_FILE:
                continue
            rel_id = f'{id_prefix}/{entry.name}' if id_prefix else entry.name
            entry_meta = meta.get(rel_id, {})
            # print(f'|{rel_id},{entry_meta}')
            if entry_meta.get('hidden'):
                continue
            is_dir = entry.is_dir()
            if not is_dir and entry.suffix.lower() not in DOC_EXTENSIONS:
                continue
            default_title = _doc_title_from_name(entry.name if is_dir else entry.stem)
            # nid = entry.name
            child = TreeNode(
                nid=rel_id, name=rel_id, title=entry_meta.get('title', default_title),
                desc=entry_meta.get('desc', ''), tags=entry_meta.get('tags', ''),
                is_leaf=not is_dir, node_type='doc',
            )
            child.data['order'] = entry_meta.get('order', "99999")
            node.add_child(child)
            if is_dir:
                add_dir(child, entry, rel_id)

    add_dir(root, docs_root, '')
    root.update_all_descendant_leafs_count()
    for nd in root.depth_first():
        nd.children.sort(key=lambda c: (c.data.get('order', "99999"), c.title))
    return root


def fix_doc_links(html, pname):
    soup = BeautifulSoup(html, 'html.parser')
    current_dir = posixpath.dirname(pname)

    for image in soup.find_all('img', src=True):
        src = image['src']
        parts = urlsplit(src)
        if (
            not parts.path
            or parts.path.startswith('/')
            or parts.scheme
            or parts.netloc
        ):
            continue
        image_path = posixpath.normpath(
            posixpath.join(current_dir, parts.path)
        )
        if image_path == 'images' or image_path.startswith('images/'):
            image['src'] = urlunsplit((
                '', '', f'/static/docs/{image_path}',
                parts.query, parts.fragment
            ))

    for a in soup.find_all('a', href=True):
        href = a['href']

        parts = urlsplit(href)

        if (
            not parts.path
            or parts.path.startswith('/')
            or parts.scheme
            or parts.netloc
        ):
            continue

        # Resolve the relative Markdown link against the current document
        target = posixpath.normpath(
            posixpath.join(current_dir, parts.path)
        )

        # Only rewrite links to documentation files
        if not target.endswith(('.md', '.html')):
            continue

        doc_url = reverse(
            'add-page-doc',
            kwargs={'pname': target}
        )

        doc_url_part = f'{doc_url}?part=1'

        a['href'] = urlunsplit((
            '',
            '',
            doc_url,
            parts.query,
            parts.fragment
        ))

        a['hx-get'] = urlunsplit((
            '',
            '',
            doc_url_part,
            parts.query,
            parts.fragment
        ))
        a['hx-target'] = 'closest .calc'
        a['hx-swap'] = 'afterend'
        a['hx-trigger'] = f"click[get_card_once('{posixpath.basename(parts.path)}__page')]"

    return str(soup)
