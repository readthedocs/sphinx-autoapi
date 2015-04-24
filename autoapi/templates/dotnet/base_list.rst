{% block title %}

{{ obj.short_name }} {{ obj.type.title() }}
{{ "=" * (obj.short_name|length + obj.type|length + 1) }}

{% endblock %}

{% block toc %}

{% if obj.children %}

{#
.. toctree::
   :hidden:
   :maxdepth: 1

   {% for item in obj.children|sort %}
   /autoapi/{{ item.id.split('.')|join('/') }}/index
   {%- endfor %}

#}

{% endif %}

{% endblock %}


{% block content %}

{%- macro display_type(item_type) %}

    .. rubric:: {{ item_type.title() }}

{%- for obj_item in obj.item_map.get(item_type, []) %}
{% macro render() %}{{ obj_item.summary }}{% endmacro %}

    {{ obj_item.type }} :dn:{{ obj_item.ref_directive }}:`{{ obj_item.short_name }}`
        {{ render()|indent(8) }}

{%- endfor %}
{%- endmacro %}

.. dn:{{ obj.ref_type }}:: {{ obj.name }}

{%- for item_type in obj.item_map.keys() %}
{{ display_type(item_type) }}
{%- endfor %}


{% endblock %}