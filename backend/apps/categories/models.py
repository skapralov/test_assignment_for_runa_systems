from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        blank=True,
        null=True,
        db_index=True,
    )

    @property
    def children(self):
        return Category.objects.filter(parent_id=self.id)

    @property
    def all_children(self):
        sql = """WITH RECURSIVE children AS (
                 SELECT *, 'self' AS status FROM categories_category WHERE id = %s
                 UNION
                 SELECT categories_category.*, 'child' AS status 
                 FROM categories_category JOIN children ON categories_category.parent_id = children.id
                 )
                 SELECT * FROM children OFFSET 1"""

        return Category.objects.raw(sql, [self.id])

    @property
    def parents(self):
        if not self.parent:
            return Category.objects.none()

        sql = """WITH RECURSIVE parents AS (
                 SELECT *, 'self' AS status FROM categories_category WHERE id = %s
                 UNION
                 SELECT categories_category.*, 'parent' AS status 
                 FROM categories_category JOIN parents ON categories_category.id = parents.parent_id
                 )
                 SELECT * FROM parents  OFFSET 1"""

        return Category.objects.raw(sql, [self.id])

    @property
    def siblings(self):
        if not self.parent:
            return Category.objects.none()

        return Category.objects.filter(parent_id=self.parent_id).exclude(id=self.id)
