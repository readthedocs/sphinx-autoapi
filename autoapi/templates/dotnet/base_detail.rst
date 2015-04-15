{% block title %}

{{ object.short_name }} {{ object.type.title()}}
{{ "=" * (object.short_name|length + object.type|length + 1) }}

.. dn:{{ object.ref_type }}:: {{ object.name }}

{% endblock %}

{% block summary %}
  {%- if object.summary %}

Summary
-------

{{ summary }}

  {%- endif %}
{% endblock %}

{% block inheritance %}
  {%- if object.inheritance %}

Inheritance Hierarchy
---------------------

    {%- for item in inheritance %}
* :dn:{{ item.ref_directive }}:`{{ item.id }}`
    {%- endfor %}
  {%- endif %}
{% endblock %}

{% block syntax %}
  {%- if object.example %}

Syntax
------

.. code-block:: csharp

   {{ example }}

  {%- endif %}
{% endblock %}


{% block content %}

  {%- macro display_type(item_type) %}
    {%- if item_type in item_map %}

{{ item_type.title() }}
{{ "-" * item_type|length }}

      {%- for obj_item in item_map.get(item_type, []) %}
{% macro render() %}{{ obj_item.render() }}{% endmacro %}
{{ render()|indent(0) }}
      {%- endfor %}
    {%- endif %}
  {%- endmacro %}

  {%- for item_type in ['constructor', 'method', 'field', 'property',
                        'event', 'operator'] %}
{{ display_type(item_type) }}
  {%- endfor %}

{% endblock %}
