from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Category, Product
from operations.decorators import admin_required, cashier_required


def parse_stock_quantity(value):
    try:
        quantity = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Enter a valid stock quantity.")
    if not quantity.is_finite() or quantity < 0 or quantity.as_tuple().exponent < -2:
        raise ValueError("Stock must be non-negative and use no more than 2 decimal places.")
    return quantity


@admin_required
def categories_list_view(request):
    context = {
        "active_icon": "products_categories",
        "categories": Category.objects.all()
    }
    return render(request, "products/categories.html", context=context)


@admin_required
def categories_add_view(request):
    context = {
        "active_icon": "products_categories",
        "category_status": Category.status.field.choices
    }

    if request.method == 'POST':
        # Save the POST arguments
        data = request.POST

        attributes = {
            "name": data['name'],
            "status": data['state'],
            "description": data['description']
        }

        # Check if a category with the same attributes exists
        if Category.objects.filter(**attributes).exists():
            messages.error(request, 'Category already exists!',
                           extra_tags="warning")
            return redirect('products:categories_add')

        try:
            # Create the category
            new_category = Category.objects.create(**attributes)

            # If it doesn't exist, save it
            new_category.save()

            messages.success(request, 'Category: ' +
                             attributes["name"] + ' created successfully!', extra_tags="success")
            return redirect('products:categories_list')
        except Exception as e:
            messages.success(
                request, 'There was an error during the creation!', extra_tags="danger")
            print(e)
            return redirect('products:categories_add')

    return render(request, "products/categories_add.html", context=context)


@admin_required
def categories_update_view(request, category_id):
    """
    Args:
        request:
        category_id : The category's ID that will be updated
    """

    # Get the category
    try:
        # Get the category to update
        category = Category.objects.get(id=category_id)
    except Exception as e:
        messages.success(
            request, 'There was an error trying to get the category!', extra_tags="danger")
        print(e)
        return redirect('products:categories_list')

    context = {
        "active_icon": "products_categories",
        "category_status": Category.status.field.choices,
        "category": category
    }

    if request.method == 'POST':
        try:
            # Save the POST arguments
            data = request.POST

            attributes = {
                "name": data['name'],
                "status": data['state'],
                "description": data['description']
            }

            # Check if a category with the same attributes exists
            if Category.objects.filter(**attributes).exclude(id=category_id).exists():
                messages.error(request, 'Category already exists!',
                               extra_tags="warning")
                return redirect('products:categories_update', category_id=category_id)

            # Get the category to update
            category = Category.objects.filter(
                id=category_id).update(**attributes)

            category = Category.objects.get(id=category_id)

            messages.success(request, '¡Category: ' + category.name +
                             ' updated successfully!', extra_tags="success")
            return redirect('products:categories_list')
        except Exception as e:
            messages.success(
                request, 'There was an error during the elimination!', extra_tags="danger")
            print(e)
            return redirect('products:categories_list')

    return render(request, "products/categories_update.html", context=context)


@admin_required
def categories_delete_view(request, category_id):
    """
    Args:
        request:
        category_id : The category's ID that will be deleted
    """
    try:
        # Get the category to delete
        category = Category.objects.get(id=category_id)
        category.delete()
        messages.success(request, '¡Category: ' + category.name +
                         ' deleted!', extra_tags="success")
        return redirect('products:categories_list')
    except Exception as e:
        messages.success(
            request, 'There was an error during the elimination!', extra_tags="danger")
        print(e)
        return redirect('products:categories_list')


@admin_required
def products_list_view(request):
    context = {
        "active_icon": "products",
        "products": Product.objects.all()
    }
    return render(request, "products/products.html", context=context)


@admin_required
def products_add_view(request):
    context = {
        "active_icon": "products_categories",
        "product_status": Product.status.field.choices,
        "product_units": Product.UNIT_CHOICES,
        "categories": Category.objects.all().filter(status="ACTIVE")
    }

    if request.method == 'POST':
        # Save the POST arguments
        data = request.POST
        try:
            stock_quantity = parse_stock_quantity(data.get('stock_quantity', '0'))
            unit = data.get('unit', 'piece')
            if unit not in dict(Product.UNIT_CHOICES):
                raise ValueError("Select a valid inventory unit.")
        except ValueError as error:
            messages.error(request, str(error))
            return redirect('products:products_add')

        attributes = {
            "name": data['name'],
            "status": data['state'],
            "description": data['description'],
            "material": data.get('material', '').strip(),
            "color": data.get('color', '').strip(),
            "size": data.get('size', '').strip(),
            "unit": unit,
            "category": Category.objects.get(id=data['category']),
            "price": data['price'],
            "stock_quantity": stock_quantity,
            "sku": data.get('sku') or None,
        }

        if Product.objects.filter(**attributes).exists():
            messages.error(request, 'Product already exists!',
                           extra_tags="warning")
            return redirect('products:products_add')

        try:
            # Create the product
            new_product = Product.objects.create(**attributes)

            # If it doesn't exist, save it
            new_product.save()

            messages.success(request, 'Product: ' +
                             attributes["name"] + ' created successfully!', extra_tags="success")
            return redirect('products:products_list')
        except Exception as e:
            messages.success(
                request, 'There was an error during the creation!', extra_tags="danger")
            print(e)
            return redirect('products:products_add')

    return render(request, "products/products_add.html", context=context)


@admin_required
def products_update_view(request, product_id):
    """
    Args:
        request:
        product_id : The product's ID that will be updated
    """

    # Get the product
    try:
        # Get the product to update
        product = Product.objects.get(id=product_id)
    except Exception as e:
        messages.success(
            request, 'There was an error trying to get the product!', extra_tags="danger")
        print(e)
        return redirect('products:products_list')

    context = {
        "active_icon": "products",
        "product_status": Product.status.field.choices,
        "product_units": Product.UNIT_CHOICES,
        "product": product,
        "categories": Category.objects.all()
    }

    if request.method == 'POST':
        try:
            # Save the POST arguments
            data = request.POST
            stock_quantity = parse_stock_quantity(data.get('stock_quantity', '0'))
            unit = data.get('unit', 'piece')
            if unit not in dict(Product.UNIT_CHOICES):
                raise ValueError("Select a valid inventory unit.")

            attributes = {
                "name": data['name'],
                "status": data['state'],
                "description": data['description'],
                "material": data.get('material', '').strip(),
                "color": data.get('color', '').strip(),
                "size": data.get('size', '').strip(),
                "unit": unit,
                "category": Category.objects.get(id=data['category']),
                "price": data['price'],
                "stock_quantity": stock_quantity,
                "sku": data.get('sku') or product.sku,
            }

            # Check if a product with the same attributes exists
            if Product.objects.filter(**attributes).exclude(id=product_id).exists():
                messages.error(request, 'Product already exists!',
                               extra_tags="warning")
                return redirect('products:products_add')

            # Get the product to update
            for field, value in attributes.items():
                setattr(product, field, value)
            product.save()

            messages.success(request, '¡Product: ' + product.name +
                             ' updated successfully!', extra_tags="success")
            return redirect('products:products_list')
        except Exception as e:
            messages.success(
                request, 'There was an error during the update!', extra_tags="danger")
            print(e)
            return redirect('products:products_list')

    return render(request, "products/products_update.html", context=context)


@admin_required
def products_delete_view(request, product_id):
    """
    Args:
        request:
        product_id : The product's ID that will be deleted
    """
    try:
        # Get the product to delete
        product = Product.objects.get(id=product_id)
        product.delete()
        messages.success(request, '¡Product: ' + product.name +
                         ' deleted!', extra_tags="success")
        return redirect('products:products_list')
    except Exception as e:
        messages.success(
            request, 'There was an error during the elimination!', extra_tags="danger")
        print(e)
        return redirect('products:products_list')


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


@cashier_required
def get_products_ajax_view(request):
    if request.method == 'GET':
        if is_ajax(request=request):
            data = []

            term = request.GET.get('term', '')
            products = Product.objects.filter(
                Q(name__icontains=term) | Q(sku__icontains=term),
                status="ACTIVE",
                stock_quantity__gt=0,
            )
            for product in products[0:10]:
                item = product.to_json()
                data.append(item)

            return JsonResponse(data, safe=False)
    return JsonResponse({"error": "Invalid product search request."}, status=400)
