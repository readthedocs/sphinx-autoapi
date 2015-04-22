{{ object.name }}
{{ "-" * object.name|length }}

{% block toc %}

{% if children %}

.. toctree::
   :hidden:
   :maxdepth: 4

   {% for item in children|sort %}
   /autoapi/{{ item.id.split('.')|join('/') }}/index
   {%- endfor %}

{% endif %}

{% endblock %}

{% if object.docstring %}

.. rubric:: Summary

{{ object.docstring }}

{% endif %}

.. module:: {{ object.name }}



{% block content %}

{%- macro display_type(item_type) %}
{%- if item_type in item_map %}

{{ item_type.title() }}
{{ "*" * item_type|length }}

{%- for obj_item in item_map.get(item_type, []) %}
{% macro render() %}{{ obj_item.render() }}{% endmacro %}
    {{ render()|indent(4) }}
{%- endfor %}
{%- endif %}
{%- endmacro %}

{%- for item_type in ['module', 'function', 'class'] %}
{{ display_type(item_type) }}
{%- endfor %}

{% endblock %}
