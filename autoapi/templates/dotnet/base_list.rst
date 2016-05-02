{% block title %}

{{ obj.name }} {{ obj.type.title() }}
{{ "=" * (obj.name|length + obj.type|length + 1) }}

{% endblock %}

{% block toc %}

{% if obj.children %}

.. toctree::
   :hidden:
   :maxdepth: 2

   {% for item in obj.children|sort %}
   {% if item.type != 'namespace' %}
   {{ item.include_path }}
   {% endif %}
   {% endfor %}


{% endif %}

{% if obj.references %}

.. toctree::
   :hidden:
   :maxdepth: 2

   {% for item in obj.references|sort %}
   {% if item.type != 'namespace' %}
   {{ item.include_path }}
   {% endif %}
   {% endfor %}

{% endif %}

{% endblock %}


{% block content %}

{%- macro display_type(item_type) %}

    .. rubric:: {{ item_type.title() }}

{%- for obj_item in obj.item_map.get(item_type, []) %}
{% macro render() %}{{ obj_item.summary }}{% endmacro %}

    {{ obj_item.type }} :dn:{{ obj_item.ref_directive }}:`{{ obj_item.ref_short_name }}`
        .. object: type={{ obj_item.type }} name={{ obj_item.ref_name }}

        {{ render()|indent(8) }}

{%- endfor %}
{%- endmacro %}

.. dn:{{ obj.ref_type }}:: {{ obj.name }}

{%- for item_type in obj.item_map.keys() %}
{{ display_type(item_type) }}
{%- endfor %}


{% endblock %}
