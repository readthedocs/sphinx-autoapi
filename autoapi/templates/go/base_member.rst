.. go:{{ obj.ref_type }}:: {{ obj.name }}

    {% macro render() %}{{ obj.docstring }}{% endmacro %}
    {{ render()|indent(4) }}

    {%- for param in obj.parameters %}
    :param {{ param.name }}: {{ param.desc }}
    {%- if param.type %}
    :type {{ param.name }}: {{ param.type }}
    {%- endif %}
    {%- endfor %}
    {%- if obj.returns %}
    :rtype: {{ obj.returns.id }}
    {%- endif %}
