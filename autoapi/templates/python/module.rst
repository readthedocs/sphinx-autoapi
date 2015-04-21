{{ object.name }}
{{ "-" * object.name|length }}

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

{%- for item_type in ['function', 'class'] %}
{{ display_type(item_type) }}
{%- endfor %}

{% endblock %}
