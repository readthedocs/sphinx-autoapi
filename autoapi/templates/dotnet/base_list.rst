{% block title %}

{{ object.short_name }} {{ object.type.title() }}
{{ "=" * (object.short_name|length + object.type|length + 1) }}

{% endblock %}

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

{% block content %}

{% if object.children %}

{%- macro display_type(item_type) %}
{%- if item_type in item_map %}

    .. rubric:: {{ item_type.title() }}

{%- for obj_item in item_map.get(item_type, []) %}
        {% macro render() %}{{ obj_item.summary }}{% endmacro %}
    {{ obj_item.type }} :dn:{{ obj_item.ref_directive }}:`{{ obj_item.short_name }}`
        {{ render()|indent(8) }}
{%- endfor %}

{%- endif %}
{%- endmacro %}

.. dn:{{ object.ref_type }}:: {{ object.name }}

{%- for item_type in ['class', 'struct', 'delegate', 'enum'] %}
{{ display_type(item_type) }}
{%- endfor %}

{% endif %}

{% endblock %}