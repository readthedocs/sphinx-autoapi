{% block title %}

{{ object.short_name }} {{ object.type.title() }}
{{ "=" * (object.short_name|length + object.type|length + 1) }}

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

.. dn:{{ object.ref_type }}:: {{ object.name }}

{% if object.children %}

    {%- for item in object.children|sort %}
        {% macro render() %}{{ item.summary }}{% endmacro %}
    {{ item.type }} :dn:{{ item.ref_directive }}:`{{ item.short_name }}`
        {{ render()|indent(8) }}
    {% endfor %}

{% endif %}

{% endblock %}
