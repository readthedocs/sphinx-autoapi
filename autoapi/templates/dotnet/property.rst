.. dn:{{ type.lower() }}:: {{ name }}

	{% if summary %}

    {% macro render() %}{{ summary }}{% endmacro %}
    {{ render()|indent(4) }}

	{% endif %}

	.. code-block:: csharp

	   {{ syntax }}
