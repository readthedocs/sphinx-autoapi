.. {{ obj.type.lower() }}:: {{ obj.name }}

	{% if summary %}

	{{ obj.summary }}

	{% endif %}

	.. code-block:: csharp

	   {{ obj.syntax.content.CSharp }}
