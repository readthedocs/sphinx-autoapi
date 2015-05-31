.. go:{{ obj.ref_type }}:: {{ obj.name }}
{%- if obj.type == 'func' -%}
  ({{ obj.parameters|map(attribute='name')|join(', ') }})
{%- endif %}

    {% macro render() %}{{ obj.docstring }}{% endmacro %}
    {{ render()|indent(4) }}

    {% for param in obj.parameters %}
    :param {{ param.name }}:
    :type {{ param.name }}: {{ param.type }}
    {%- endfor %}
    {%- if obj.returns %}
    :rtype: {{ obj.returns.id }}
    {%- endif %}
