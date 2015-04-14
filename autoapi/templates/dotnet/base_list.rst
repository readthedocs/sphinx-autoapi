{% block title %}

{{ short_name }} {{ type.title()}}
{{ "=" * (short_name|length + type|length + 1) }}

{% endblock %}

{% block toc %}

{% if children %}

.. toctree::
   :hidden:

   {% for item in children %}
   /autoapi/{{ item.id.split('.')|join('/') }}/index
   {%- endfor %}

{% endif %}

{% endblock %}

{% block table %}

{% if children %}

.. list-table:: Classes
   :widths: 20, 80
   :header-rows: 1

   * - Class
     - Description
   {%- for item in children %}
   {% macro render() %}{{ item.summary }}{% endmacro %}
   * - :dn:{{ item.type.lower().replace('class', 'cls').replace('interface', 'iface').replace('delegate', 'del') }}:`{{ item.id }}`
     - {{ render()|indent(7) }}
   {% endfor %}

{% endif %}

{% endblock %}
