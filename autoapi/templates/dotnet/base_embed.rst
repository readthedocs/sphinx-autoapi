.. dn:{{ object.ref_type }}:: {{ object.name }}

    {% if summary %}

    {% macro render() %}{{ summary }}{% endmacro %}
    {{ render()|indent(4) }}

    {% endif %}

    {%- for param in parameters %}
    :param {{ param.name }}: {{ param.desc }}
      {%- if param.type %}
    :type {{ param.name }}: {{ param.type }}
      {%- endif %}
    {%- endfor %}

    .. code-block:: csharp

       {{ example }}
