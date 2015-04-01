{{ fullname }}
{{ underline }}

{% if docstring %}

.. rubric:: Summary

{{ docstring }}

{% endif %}

.. module:: {{ fullname }}


{% if classes %}

.. rubric:: Classes

{% for class in classes %}

{{ class.render() }}

{% endfor %}

{% endif %}


{% if methods %}

.. rubric:: Functions

{% for method in methods %}

{{ method.render() }}

{% endfor %}

{% endif %}