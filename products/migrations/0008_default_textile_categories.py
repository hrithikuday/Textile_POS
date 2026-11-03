from django.db import migrations


DEFAULT_CATEGORIES = (
    ("Fabrics & Dress Materials", "Fabric sold by the meter, yard, or roll."),
    ("Sarees", "Sarees and related traditional garments."),
    ("Kurtis & Kurtas", "Kurtis, kurtas, and tunics."),
    ("Shirts & Tops", "Shirts, blouses, and tops."),
    ("Dresses & Gowns", "Dresses, gowns, and one-piece garments."),
    ("Bottom Wear", "Trousers, skirts, leggings, and other bottom wear."),
    ("Dupattas & Shawls", "Dupattas, shawls, scarves, and wraps."),
    ("Kidswear", "Clothing and garments for children."),
    ("Home Textiles", "Bed linen, towels, curtains, and home fabrics."),
    ("Accessories", "Textile accessories and garment add-ons."),
)


def add_default_categories(apps, schema_editor):
    Category = apps.get_model("products", "Category")
    database = schema_editor.connection.alias
    existing_names = {
        name.strip().casefold()
        for name in Category.objects.using(database).values_list("name", flat=True)
    }

    for name, description in DEFAULT_CATEGORIES:
        normalized_name = name.casefold()
        if normalized_name in existing_names:
            continue
        Category.objects.using(database).create(
            name=name,
            description=description,
            status="ACTIVE",
        )
        existing_names.add(normalized_name)


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0007_product_product_stock_nonnegative"),
    ]

    operations = [
        migrations.RunPython(add_default_categories, migrations.RunPython.noop),
    ]
