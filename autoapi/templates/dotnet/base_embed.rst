.. dn:{{ obj.ref_type }}:: {{ obj.name }}

    {% if obj.summary %}

    {% macro render() %}{{ summary }}{% endmacro %}
    {{ render()|indent(4) }}

    {% endif %}

    {%- for param in obj.parameters %}
    :param {{ param.name }}: {{ param.desc }}
    {%- if param.type %}
    :type {{ param.name }}: {{ param.type }}
    {%- endif %}
    {%- endfor %}
    {%- if obj.returns %}
    :rtype: {{ obj.returns.id }}
    {%- endif %}

    {% if obj.example %}
    .. code-block:: csharp

       {{ obj.example }}
    {%- endif %}
