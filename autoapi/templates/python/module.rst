{{ obj.name }}
{{ "-" * obj.name|length }}

{% block toc %}

{% if obj.children %}

.. toctree::
   :maxdepth: 4

   {% for item in obj.children|sort %}
   /autoapi/{{ item.id.split('.')|join('/') }}/index
   {%- endfor %}

{% endif %}

{% endblock %}

{% if obj.docstring %}

.. rubric:: Summary

{{ obj.docstring }}

{% endif %}

.. py:module:: {{ obj.name }}




{% block content %}
{%- for obj_item in obj.children|sort %}

{% macro render() %}{{ obj_item.render() }}{% endmacro %}
{{ render()|indent(0) }}

{%- endfor %}
{% endblock %}

