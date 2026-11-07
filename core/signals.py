"""Clean user-written text on every save (see core/sanitize.py).

One map here instead of a save() override per model. Note that
QuerySet.update() bypasses signals, so views that bulk-update user text
must call clean_text themselves.
"""
from django.apps import apps
from django.db.models.signals import pre_save

from core.sanitize import clean_fields

# (app_label, ModelName): (plain-text fields, rich-text fields)
CLEAN_FIELDS = {
    ('messaging', 'Message'): ((), ('content',)),
    ('messaging', 'Conversation'): (('name',), ()),
    ('messaging', 'Poll'): (('question',), ()),
    ('messaging', 'PollOption'): (('text',), ()),
    ('tasks', 'Task'): (('title', 'description', 'reference_number', 'location_name'), ()),
    ('tasks', 'TaskComment'): (('message',), ()),
    ('tasks', 'Correspondence'): (('title', 'description', 'reference_number'), ()),
    ('tasks', 'CorrespondenceAcknowledgement'): (('note',), ()),
    ('tasks', 'TaskTodo'): (('title', 'description'), ()),
    ('tasks', 'Todo'): (('title', 'description'), ()),
    ('submissions', 'Submission'): (('notes', 'manager_feedback'), ()),
    ('submissions', 'SubmissionComment'): (('comment',), ()),
    ('submissions', 'SubmissionVersion'): (('notes',), ()),
    ('submissions', 'SubmissionFieldValue'): (('value',), ()),
    ('notifications', 'Notification'): (('title', 'message'), ()),
    ('work_modules', 'WorkModule'): (('name', 'description'), ()),
    ('work_modules', 'WorkGroup'): (('name', 'description'), ()),
    ('users', 'CustomUser'): (('first_name', 'last_name'), ()),
    ('users', 'Department'): (('name', 'description'), ()),
}


def _make_receiver(plain, rich):
    def _clean(sender, instance, raw=False, **kwargs):
        if raw:  # loaddata: keep fixtures exactly as written
            return
        clean_fields(instance, plain=plain, rich=rich)
    return _clean


_receivers = []


def connect():
    for (app_label, model_name), (plain, rich) in CLEAN_FIELDS.items():
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            continue
        plain = tuple(f for f in plain if hasattr(model, f) or f in {x.name for x in model._meta.get_fields()})
        receiver = _make_receiver(plain, rich)
        _receivers.append(receiver)  # keep a strong reference
        pre_save.connect(receiver, sender=model, dispatch_uid=f'wt-clean-{app_label}-{model_name}')
