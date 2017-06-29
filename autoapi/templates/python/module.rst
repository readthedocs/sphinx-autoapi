{% if obj.docstring or obj.children %}

{{ obj.name }}
{{ "=" * obj.name|length }}

.. py:module:: {{ obj.name }}

{% endif %}

{%- if obj.docstring %}

.. autoapi-nested-parse::

   {{ obj.docstring|prepare_docstring|indent(3) }}

{% endif %}

{% block content %}
{%- for obj_item in obj.children %}

{{ obj_item.rendered|indent(0) }}

{%- endfor %}
{% endblock %}
