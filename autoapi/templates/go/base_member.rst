{% if obj.type == 'func' %}
    {# Creating the parameters line #}
    {% set ns = namespace(tmpstring='') %}
    {% set argjoin = joiner(', ') %}
    {% for param in obj.parameters %}
        {% set ns.tmpstring = ns.tmpstring ~ argjoin() ~ param.name ~ ' ' ~ param.type %}
    {% endfor %}
.. {{ obj.ref_type }}:: {{ obj.name }}({{ ns.tmpstring }})
{% else %}
.. go:{{ obj.ref_type }}:: {{ obj.name }}
{% endif %}

{% macro render() %}{{ obj.docstring }}{% endmacro %}
{{ render()|indent(4) }}

{# Don't define parameter description here, that can be done in the block
above #}
{% for param in obj.parameters %}
:param {{ param.name }}:
:type {{ param.name }}: {{ param.type }}
{% endfor %}
{% if obj.returns %}
:rtype: {{ obj.returns.type }}
{% endif %}

{% if obj.children %}
    {% for child in obj.children|sort %}
{% macro render_child() %}{{ child.render() }}{% endmacro %}
{{ render_child()|indent(4) }}
    {% endfor %}
{% endif %}

