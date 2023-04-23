# API Reference

This page contains auto-generated API reference documentation [^f1].

{{ md_fence }}{toctree}
:titlesonly:

{% for page in pages %}
{% if page.top_level_object and page.display %}
{{ page.include_path }}
{% endif %}
{% endfor %}
{{ md_fence }}

[^f1]: Created with [sphinx-autoapi](https://github.com/readthedocs/sphinx-autoapi)
