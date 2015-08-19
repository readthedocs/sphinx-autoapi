{{ obj.name }}
{{ "-" * obj.name|length }}

{% block toc %}

{% if obj.children %}

.. toctree::
   :maxdepth: 4

   {% for item in obj.children|sort %}
   /autoapi/{{ item.pathname }}/index
   {%- endfor %}

{% endif %}

{% endblock %}

{% if obj.docstring %}

.. rubric:: Summary

{{ obj.docstring }}

{% endif %}

.. js:module:: {{ obj.name }}



{% block content %}

{%- macro display_type(item_type) %}

{{ item_type.title() }}
{{ "*" * item_type|length }}

{%- for obj_item in obj.item_map.get(item_type, []) %}
{% macro render() %}{{ obj_item.render() }}{% endmacro %}

	{{ render()|indent(4) }}

{%- endfor %}
{%- endmacro %}

{%- for item_type in obj.item_map.keys() %}
{% if item_type.lower() != 'module' %}
{{ display_type(item_type) }}
{% endif %}
{%- endfor %}

{% endblock %}
