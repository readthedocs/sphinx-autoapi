{% if obj.docstring or obj.subpackages or obj.submodules or obj.children %}
:mod:`{{ obj.name }}`
======={{ "=" * obj.name|length }}

.. py:module:: {{ obj.name }}

{% endif %}

{%- if obj.docstring %}

.. autoapi-nested-parse::

   {{ obj.docstring|prepare_docstring|indent(3) }}

{% endif %}

{% block subpackages %}{% if obj.subpackages %}
Subpackages
-----------
.. toctree::
   :titlesonly:
   :maxdepth: 3
{% for subpackage in obj.subpackages %}
   {{ subpackage.short_name }}/index.rst
{%- endfor %}
{% endif %}{% endblock %}

{% block submodules %}{% if obj.submodules %}
Submodules
----------
.. toctree::
   :titlesonly:
   :maxdepth: 1
{% for submodule in obj.submodules %}
   {{ submodule.short_name }}/index.rst
{%- endfor %}
{% endif %}{% endblock %}


{% block content %}{% if obj.children %}
{{ obj.type|title }} Contents
{{ "-" * obj.type|length }}---------

{% if include_summaries %}
{% block classes %}{% if obj.classes %}
Classes
~~~~~~~

.. autoapisummary::
{% for klass in obj.classes %}
   {{ klass.id }}
{%- endfor %}
{% endif %}{% endblock %}

{% block methods %}{% if obj.methods %}
Methods
~~~~~~~

.. autoapisummary::

{% for method in obj.methods %}
   {{ method.id }}
{%- endfor %}
{% endif %}{% endblock %}

{% block functions %}{% if obj.functions %}
Functions
~~~~~~~~~
.. autoapisummary::

{% for function in obj.functions %}
   {{ function.id }}
{%- endfor %}
{% endif %}{% endblock %}
{% endif %}

{%- for obj_item in obj.children %}

{{ obj_item.rendered|indent(0) }}

{% endfor %}
{% endif %}{% endblock %}
