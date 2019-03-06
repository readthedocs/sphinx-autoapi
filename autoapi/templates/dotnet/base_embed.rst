.. dn:{{ obj.ref_type }}:: {{ obj.name }}

    {% if obj.summary %}
    {{ obj.summary|indent(4) }}

    {% endif %}

    {% for param in obj.parameters %}

    {% if param.desc %}
    :param {{ param.name }}: {{ param.desc|indent(8) }}
    {% endif %}
    {% if param.type %}
    :type {{ param.name }}: {{ param.type|indent(8) }}
    {% endif %}
    {% endfor %}

    {% if obj.returns.type %}
    :rtype: {{ obj.returns.type|indent(8) }}
    {% endif %}
    {% if obj.returns.description %}
    :return: {{ obj.returns.description|indent(8) }}
    {% endif %}

    {% if obj.example %}
    .. code-block:: csharp

        {{ obj.example|indent(8) }}
    {% endif %}
