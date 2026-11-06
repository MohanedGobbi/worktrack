from django import template
from tasks.models import Task
from work_modules.models import WorkModule, TemplateModule, TemplateTask

register = template.Library()

@register.simple_tag
def get_total_template_uses(templates):
    """
    Returns the total number of times any template in the queryset has been used.
    Used by the stats grid on the template dashboard.
    """
    if not templates:
        return 0
    # Use the correct field name 'template' as defined in WorkModule model
    return WorkModule.objects.filter(template__in=templates).count()

@register.simple_tag
def get_total_template_tasks(templates):
    """
    Returns the total number of template tasks defined across all given templates.
    """
    if not templates:
        return 0
    return TemplateTask.objects.filter(template__in=templates).count()
