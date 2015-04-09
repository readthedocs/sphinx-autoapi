{% block title %}

{{ short_name }} {{ type.title()}}
{{ "=" * (short_name|length + type|length + 1) }}

.. dn:{{ type.lower().replace('struct', 'structure').replace('enum', 'enumeration') }}:: {{ name }}

{% endblock %}

{% block summary %}

Summary
-------

{{ summary }}

{% endblock %}

{% block inheritance %}

Inheritance Hierarchy
---------------------

{% for item in inheritance %}
* :ref:`{{ item.id }}`
{% endfor %}

{% endblock %}

{% block syntax %}

Syntax
------

.. code-block:: csharp

   {{ syntax }}

{% endblock %}


{% block content %}

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

{% endblock %}
