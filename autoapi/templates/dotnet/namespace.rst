{{ name.CSharp }} Namespace
{{ underline }}{{ underline }}

Tree:

.. toctree::
   :hidden:
   {% for obj in items %} 
   /autoapi/{{ obj.type }}/{{ obj.id.split('.')[-1] }} {% endfor %}


Table:


{% if items %}

.. list-table:: Classes
   :widths: 20, 80
   :header-rows: 1

   * - Class
     - Description
{% for obj in items %} {% macro render() %}{{ obj.summary }}{% endmacro %}
   * - :dn:{{ obj.type.lower().replace('class', 'cls').replace('interface', 'iface') }}:`{{ obj.id }}`
     - {{ render()|indent(7) }}
{% endfor %}



{% endif %}