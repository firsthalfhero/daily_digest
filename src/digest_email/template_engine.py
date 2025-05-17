import os
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound
from typing import Any, Dict

class EmailTemplateEngine:
    def __init__(self, template_dir: str = None):
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            cache_size=50
        )
        self.template_dir = template_dir

    def render(self, template_name: str, context: Dict[str, Any], plain: bool = False) -> str:
        """
        Render a template with the given context.
        If plain=True, render the plain text version, else HTML.
        """
        ext = 'txt' if plain else 'html'
        template_file = f"{template_name}.{ext}"
        try:
            template = self.env.get_template(template_file)
        except TemplateNotFound:
            raise ValueError(f"Template '{template_file}' not found in '{self.template_dir}'")
        return template.render(**context) 