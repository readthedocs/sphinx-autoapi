{% block title %}

{{ object.short_name }} {{ object.type.title()}}
{{ "=" * (object.short_name|length + object.type|length + 1) }}

.. dn:{{ object.type }}:: {{ object.name }}

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
   * - :dn:{{ item.ref_type }}:`{{ item.id }}`
     - {{ render()|indent(7) }}
   {% endfor %}

{% endif %}

{% endblock %}
