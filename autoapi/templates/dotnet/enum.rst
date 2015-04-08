{{ short_name }} {{ type.title()}}
{{ "=" * (short_name|length + type|length + 1) }}

.. dn:enumeration:: {{ name }}

Summary
-------

{{ summary }}

Inheritance Hierarchy
---------------------

{% for item in inheritance %}
* :ref:`{{ item.id }}`
{% endfor %}

Syntax
------

.. code-block:: csharp

   {{ syntax }}

{% if item_map %}

{% for obj_type, obj_list in item_map.items() %}

{{ obj_type }}
{{ "-" * obj_type|length }}

{% for obj_item in obj_list %}
{% macro render() %}{{ obj_item.render() }}{% endmacro %}
{{ render()|indent(0) }}
{% endfor %}

{% endfor %}

{% endif %}