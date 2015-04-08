{{ short_name }} {{ type.title()}}
{{ "=" * short_name|length }}{{ "=" * type|length }}=

Tree:

{% if children %}

.. toctree::
   :hidden:
   {% for item in children %} 
   /autoapi/{{ item.type }}/{{ item.id.split('.')[-1] }} {% endfor %}

{% endif %}

Table:


{% if children %}

.. list-table:: Classes
   :widths: 20, 80
   :header-rows: 1

   * - Class
     - Description
{% for item in children %} {% macro render() %}{{ item.summary }}{% endmacro %}
   * - :dn:{{ item.type.lower().replace('class', 'cls').replace('interface', 'iface').replace('delegate', 'del') }}:`{{ item.id }}`
     - {{ render()|indent(7) }}
{% endfor %}



{% endif %}