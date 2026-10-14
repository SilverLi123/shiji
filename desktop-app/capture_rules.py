"""Auditable local suggestions; canonical tags, existing categories, no AI service."""
from dataclasses import dataclass
import re
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Rule:
    name: str
    domains: tuple
    terms: tuple
    category: str
    tags: tuple


RULES = (
    Rule('models', ('huggingface.co',), (), '开发工具', ('AI', '模型')),
    Rule('3d-assets', ('polyhaven.com', 'ambientcg.com', 'sketchfab.com'), (), '3D', ('3D', '素材')),
    Rule('motion', ('gsap.com', 'reactbits.dev', 'motionsites.ai'), (r'\bgsap\b',), 'UI / 设计', ('动效', '前端')),
    Rule('react-components', (), (r'\breact\b.*\b(component|components|library|ui)\b', r'React.*组件'), 'UI / 设计', ('React', '组件')),
    Rule('github', ('github.com',), (), '开发工具', ('GitHub',)),
    Rule('inspiration', ('recent.co', 'awwwards.com'), (), '灵感', ('设计',)),
)


def suggest(resource, metadata):
    host = (urlsplit(resource['url']).hostname or '').lower().removeprefix('www.')
    content = ' '.join(str(metadata.get(k, '') or resource.get(k, '')) for k in ('title', 'description'))[:1600]
    matched = [r for r in RULES if host in r.domains or any(re.search(p, content, re.I) for p in r.terms)]
    if not matched:
        return {}
    return {'category': matched[0].category, 'tags': list(dict.fromkeys(t for r in matched for t in r.tags)),
            'rules': [r.name for r in matched]}
