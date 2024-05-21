# routes.py
from flask import Flask, render_template, request, redirect, url_for, Blueprint, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os.path
import RunFirstSettings
import uuid
import mimetypes
from PIL import Image
import barterswap
import barterswapdb

item_handlers = Blueprint('item_handlers', __name__, static_folder='static', template_folder='templates')


@item_handlers.route('/add', methods=['GET', 'POST'])
def add_item():
    if 'user_id' not in session:
        flash("You need to sign in first", "error")
        return redirect(url_for('user_handlers.signin'))  #

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        category = request.form['category']
        condition = request.form['condition']
        random_filename = barterswap.upload_and_give_name('static/images', request.files['image'],
                                                          barterswap.ALLOWED_ADDITEM_IMAGE_TYPES)

        validations = [(name, 100, "Item name cannot exceed 100 characters"),
                       (description, 500, "Description cannot exceed 500 characters"),
                       (price, 10, "Price value cannot exceed 10 characters")]

        for field, max_length, error_message in validations:
            if len(field) > max_length:
                return redirect(url_for('item_handlers.add_item'))

        user_id = session['user_id']
        barterswapdb.insert_item(user_id, name, description, category, price, condition, random_filename)
        return redirect(url_for('home.home'))
    else:
        return render_template('additem.html', max_content_length=barterswap.max_content_length,
                               ALLOWED_IMAGE_TYPES=barterswap.ALLOWED_ADDITEM_IMAGE_TYPES)


@item_handlers.route('/<int:item_id>')
def get_item(item_id):
    # TODO what if item does not exists?
    print(barterswapdb.get_itemdata_by_id(item_id, ["item_id"]), 12312321321)

    item = barterswapdb.get_itemdata_by_id(item_id, "*")
    print(barterswapdb.get_user_balance(item[1]), 123123213215555)
    print(barterswapdb.get_user_balance(float(item[1])), item[1] + 1)
    print(barterswapdb.get_user_balance(float(item[1])))
    seller = barterswapdb.get_userdata_by_user_id(item[1], ["username"])

    item[7] = item[7] if item[7] and os.path.exists("static/images/%s" % item[7]) else 'default.png'
    bids = barterswapdb.get_top_bids_by_item_id(item_id)
    return render_template('item.html', item=tuple(item), bids=bids, seller=seller)


@item_handlers.route('/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(item_id):
    # NEED  update

    if 'user_id' not in session:
        flash("You need to sign in first", "error")
        return redirect(url_for('user_handlers.signin'))

    if request.method == 'POST':
        user_id = session['user_id']
        if not barterswapdb.is_user_owns_the_item(user_id, item_id):
            flash("You do not have access to edit this item!", "error")
            return redirect(url_for('home.home'))
        # TODO image editing will be added
        name = request.form['name']
        description = request.form['description']
        # category = request.form['category']
        # condition = request.form['condition']
        if 'is_new_image' in request.form and request.form['is_new_image'] == 'on':
            random_filename = barterswap.upload_and_give_name('static/images', request.files['image'],
                                                              barterswap.ALLOWED_ADDITEM_IMAGE_TYPES)
            barterswapdb.update_item_v1(name, description, random_filename, item_id)
        else:
            barterswapdb.update_item_v2(name, description, item_id)
        return redirect(url_for('item_handlers.get_item', item_id=item_id))
    elif request.method == 'GET':
        item = barterswapdb.get_itemdata_by_id(item_id, "*")
        item[7] = item[7] if item[7] and os.path.exists("static/images/%s" % item[7]) else 'default.png'
        return render_template('edititem.html', item=item, max_content_length=barterswap.max_content_length,
                               ALLOWED_IMAGE_TYPES=barterswap.ALLOWED_ADDITEM_IMAGE_TYPES)
