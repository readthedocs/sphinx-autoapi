.. go:{{ obj.ref_type }}:: {{ obj.name }}

    {%- for param in obj.parameters %}
    :param {{ param.name }}: {{ param.desc }}
    {%- if param.type %}
    :type {{ param.name }}: {{ param.type }}
    {%- endif %}
    {%- endfor %}
    {%- if obj.returns %}
    :rtype: {{ obj.returns.id }}
    {%- endif %}
