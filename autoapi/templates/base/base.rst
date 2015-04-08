.. {{ type.lower() }}:: {{ name }}

	{% if summary %}

	{{ summary }}

	{% endif %}

	.. code-block:: csharp

	   {{ syntax.content.CSharp }}
