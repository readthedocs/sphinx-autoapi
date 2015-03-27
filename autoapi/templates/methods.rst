{# Identention in this file is important #}
   {% block methods %}

   {% if methods %}
   
   .. rubric:: Methods

   {% for item in methods %}

   .. method:: {{ item.qualifiedName.CSharp }}

   .. code-block:: csharp

	   {{ item.syntax.content.CSharp }}

   {%- endfor %}
   {% endif %}
   {% endblock %}