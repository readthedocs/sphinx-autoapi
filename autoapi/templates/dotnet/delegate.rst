{{ short_name }}
{{  "=" * short_name|length }}

.. dn:delegate:: {{ name }}

	{% if summary %}

    {% macro render() %}{{ summary }}{% endmacro %}
    {{ render()|indent(4) }}

	{% endif %}

	.. code-block:: csharp

	   {{ syntax }}
