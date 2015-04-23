

{% block title %}

{{ obj.short_name }} {{ obj.type.title()}}
{{ "=" * (obj.short_name|length + obj.type|length + 1) }}

.. dn:{{ obj.ref_type }}:: {{ obj.name }}

{% endblock %}

.. contents:: 

{% block summary %}
  {%- if obj.summary %}
Summary
-------

{{ obj.summary }}

  {%- endif %}
{% endblock %}

{% block inheritance %}
  {%- if obj.inheritance %}

Inheritance Hierarchy
---------------------

    {%- for item in inheritance %}
* :dn:{{ item.ref_directive }}:`{{ item.id }}`
    {%- endfor %}
  {%- endif %}
{% endblock %}

{% block syntax %}
  {%- if obj.example %}

Syntax
------

.. code-block:: csharp

   {{ obj.example }}

  {%- endif %}
{% endblock %}


{% block content %}

  {%- macro display_type(item_type) %}
    {%- if item_type in obj.item_map %}

{{ item_type.title() }}
{{ "-" * item_type|length }}

      {%- for obj_item in obj.item_map.get(item_type, []) %}
{% macro render() %}{{ obj_item.render() }}{% endmacro %}
{{ render()|indent(0) }}
      {%- endfor %}
    {%- endif %}
  {%- endmacro %}

  {%- for item_type in obj.item_map.keys() %}
{{ display_type(item_type) }}
  {%- endfor %}

{% endblock %}
