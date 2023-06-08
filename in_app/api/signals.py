from django.db.models.signals import post_save
from django.dispatch import receiver

from in_app.models import WashCategoryItemRelation, WashItem, ItemWithCount


@receiver(post_save, sender=WashCategoryItemRelation)
def update_item_count_on_relation_save(sender, instance, items_from_api=[], **kwargs):
    # Create or update ItemWithCount objects for each item_from_api
    for item_from_api in items_from_api:
        item = WashItem.objects.get(id=item_from_api['id'])
        item_with_count, created = ItemWithCount.objects.get_or_create(item=item, relation=instance)
        item_with_count.count = item_from_api['count']
        item_with_count.save()
    instance.save()
