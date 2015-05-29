.. go:package:: {{ obj.name }}

{{ obj.name }}
{{ "=" * obj.name|length }}

{% block toc %}
  {%- if obj.children %}

.. toctree::
   :maxdepth: 4

   {% for item in obj.children|sort %}
   /autoapi/{{ item.id.split('.')|join('/') }}/index
   {%- endfor %}

  {%- endif %}
{% endblock %}

{% if obj.docstring %}
{{ obj.docstring }}
{% endif %}

{% block content %}




{%- for item_type in obj.item_map.keys() %}

{{ item_type.title() }}
{{ "-" * item_type.title()|length }}

{%- for obj_item in obj.item_map.get(item_type, []) %}

{% macro render() %}{{ obj_item.render() }}{% endmacro %}
{{ render()|indent(0) }}

{%- endfor %}
{%- endfor %}

{% endblock %}
