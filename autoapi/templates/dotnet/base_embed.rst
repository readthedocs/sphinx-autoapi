.. dn:{{ obj.ref_type }}:: {{ obj.name }}

    {% if obj.summary %}

    {{ obj.summary|indent(4) }}

    {% endif %}

    {%- for param in obj.parameters %}
    :param {{ param.name }}: {{ param.desc }}
    {%- if param.type %}
    :type {{ param.name }}: {{ param.type }}
    {%- endif %}
    {%- endfor %}
    {%- if obj.returns.type %}
    :rtype: {{ obj.returns.type }}
    {%- endif %}
    {%- if obj.returns.description %}
    :return: {{ obj.returns.description }}
    {%- endif %}

    {% if obj.example %}
    .. code-block:: csharp

       {{ obj.example }}
    {%- endif %}
