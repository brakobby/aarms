# school/templatetags/result_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """{{ result_dict|get_item:student.id }}"""
    return dictionary.get(key)

@register.filter
def filter_by_academic_year(assignments, academic_year):
    return [a for a in assignments if a.academic_year == academic_year]