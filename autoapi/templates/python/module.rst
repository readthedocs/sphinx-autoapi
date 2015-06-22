{{ obj.name }}
{{ "~" * obj.name|length }}

{%- if obj.docstring %}

.. rubric:: Summary

{{ obj.docstring }}

{% endif %}

.. py:module:: {{ obj.name }}

{% block content %}
{%- for obj_item in obj.children %}

{{ obj_item.rendered|indent(0) }}

{%- endfor %}
{% endblock %}

