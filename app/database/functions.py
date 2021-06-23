import django
from django.apps import apps
from datetime import datetime
import sys
django.setup()


def uniqueField(model, table, field):
    Model = apps.get_model('database', model)
    rows = Model.objects.raw('SELECT * FROM {} WHERE id IN (SELECT MIN(id) FROM database_stock GROUP BY {}) ORDER BY {}'.format(table, field, field))

    return rows



def dynamicUpdateCreate(data, find):
    """ 
    Parameters
    ----------
    data :  dict
            Data must conform to this structure:
                data = {
                    'Model': {
                    'column': value
                    },
                }
    find :  QuerySet object

    Returns
    -------
    boolean|string
    """
    if (isinstance(data, dict)):
        for model, values in data.items():
            Model = apps.get_model('database', model)
            Model.objects.update_or_create(
                stock=find,
                defaults=values,
            )
    else:
        return 'Data must be in dict structure'

    return True


def model_items_to_update(model):
    """ 
    Parameters
    ----------
    record :  Database model
              Collects all records which haven't been updated today. 
    Returns
    -------
    list
    """
    update_needed = []
    Model = apps.get_model('database', model)
    for record in Model.objects.all():

        updated = record.updated_at.date()
        today = date.today()
        if (updated == today):
            needs_update.append(record)

    return update_needed
