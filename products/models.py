from django.db import models
from django.forms import model_to_dict
from uuid import uuid4


class Category(models.Model):
    STATUS_CHOICES = (  # new
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive")
    )

    name = models.CharField(max_length=256)
    description = models.TextField(max_length=256)
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=100,
        verbose_name="Status of the category",
    )

    class Meta:
        # Table's name
        db_table = "Category"
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    STATUS_CHOICES = (  # new
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive")
    )
    UNIT_CHOICES = (
        ("piece", "Piece"),
        ("meter", "Meter"),
        ("yard", "Yard"),
        ("roll", "Roll"),
        ("kg", "Kilogram"),
    )

    name = models.CharField(max_length=256)
    description = models.TextField(max_length=256)
    material = models.CharField(max_length=120, blank=True)
    color = models.CharField(max_length=80, blank=True)
    size = models.CharField(max_length=80, blank=True)
    unit = models.CharField(max_length=12, choices=UNIT_CHOICES, default="piece")
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=100,
        verbose_name="Status of the product",
    )
    category = models.ForeignKey(
        Category, related_name="category", on_delete=models.CASCADE, db_column='category')

    price = models.FloatField(default=0)
    sku = models.CharField(max_length=64, unique=True, blank=True, null=True)
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        # Table's name
        db_table = "Product"
        constraints = [
            models.CheckConstraint(
                check=models.Q(stock_quantity__gte=0),
                name="product_stock_nonnegative",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = "TX-{}".format(uuid4().hex[:10].upper())
        super().save(*args, **kwargs)

    def to_json(self):
        item = model_to_dict(self)
        item['id'] = self.id
        item['category'] = self.category.name
        item['text'] = "{} ({})".format(self.name, self.sku)
        item['quantity'] = float(min(1, self.stock_quantity))
        item['stock_quantity'] = float(self.stock_quantity)
        item['price'] = float(self.price)
        item['total_product'] = 0
        return item
