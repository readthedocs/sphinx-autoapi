{{ name.CSharp }}
{{ underline }}

.. dn:structure:: {{ qualifiedName.CSharp }}

	{% if summary %}

    {% macro render() %}{{ summary }}{% endmacro %}
    {{ render()|indent(4) }}

	{% endif %}

	.. code-block:: csharp

	   {{ syntax.content.CSharp }}
