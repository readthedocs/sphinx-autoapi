{% block title %}

{{ obj.short_name }} {{ obj.type.title()}}
{{ "=" * (obj.short_name|length + obj.type|length + 1) }}

{% endblock %}

{% block summary %}
  {%- if obj.summary %}

{{ obj.summary }}

  {%- endif %}
{% endblock %}

{%- if obj.namespace %}
Namespace
    :dn:ns:`{{ obj.namespace }}`
{%- endif %}
{%- if obj.assemblies %}
Assemblies
  {%- for assembly in obj.assemblies %}
    * {{ assembly }}
  {%- endfor %}
{%- endif %}

----

.. contents::
   :local:

{% block inheritance %}

{%- if obj.inheritance %}

Inheritance Hierarchy
---------------------

{% for item in obj.inheritance %}
* :dn:{{ item.ref_directive }}:`{{ item.ref_name }}`
    {%- endfor %}
* :dn:{{ obj.ref_directive }}:`{{ obj.ref_name }}`
{% endif %}

{% endblock %}

{% block syntax %}

{% if obj.example %}

Syntax
------

.. code-block:: csharp

    {{ obj.example|indent(4) }}

{% endif %}

{% endblock %}


{% block content %}

.. dn:{{ obj.ref_type }}:: {{ obj.definition }}
    :hidden:

.. dn:{{ obj.ref_type }}:: {{ obj.name }}

{%- for item_type in obj.item_map.keys() %}
{%- if item_type in obj.item_map %}

{{ item_type.title() }}
{{ "-" * item_type|length }}

.. dn:{{ obj.ref_type }}:: {{ obj.name }}
    :noindex:
    :hidden:

    {% for obj_item in obj.item_map.get(item_type, []) %}
    {{ obj_item.render()|indent(4) }}
    {% endfor %}

{%- endif %}
{%- endfor %}

{% endblock %}
