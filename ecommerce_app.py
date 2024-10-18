import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime

# CSV file paths
PRODUCTS_CSV = 'products.csv'
CART_CSV = 'cart.csv'
PURCHASE_HISTORY_CSV = 'purchase_history.csv'

# Initialize the products DataFrame
def initialize_csv(file_path, columns):
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_path, index=False)

initialize_csv(PRODUCTS_CSV, ['id', 'name', 'brand', 'description', 'price', 'category', 'stock', 'release_date', 'image', 'available'])
initialize_csv(CART_CSV, ['id', 'name', 'brand', 'price', 'quantity', 'image'])
initialize_csv(PURCHASE_HISTORY_CSV, ['id', 'name', 'brand', 'price', 'quantity', 'purchase_date', 'image'])

# Functions to read and write CSV files
def read_products():
    return pd.read_csv(PRODUCTS_CSV)

def read_cart():
    try:
        return pd.read_csv(CART_CSV)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=['id', 'name', 'brand', 'price', 'quantity', 'image'])

def read_purchase_history():
    try:
        return pd.read_csv(PURCHASE_HISTORY_CSV)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=['id', 'name', 'brand', 'price', 'quantity', 'purchase_date', 'image'])

def add_product(product):
    products_df = read_products()
    products_df = products_df.append(product, ignore_index=True)
    products_df.to_csv(PRODUCTS_CSV, index=False)

def add_to_cart(product):
    cart_df = read_cart()
    # Check if the product is already in the cart
    if any(cart_df['id'] == product['id']):
        cart_df.loc[cart_df['id'] == product['id'], 'quantity'] += product['quantity']
    else:
        cart_df = cart_df.append(product, ignore_index=True)
    cart_df.to_csv(CART_CSV, index=False)

def remove_from_cart(product_id):
    cart_df = read_cart()
    cart_df = cart_df[cart_df['id'] != product_id]  # Remove the product with the given ID
    cart_df.to_csv(CART_CSV, index=False)

def checkout():
    cart = read_cart()
    if not cart.empty:
        purchase_history = read_purchase_history()
        for index, row in cart.iterrows():
            purchase = {
                'id': row['id'],
                'name': row['name'],
                'brand': row['brand'],
                'price': row['price'],
                'quantity': row['quantity'],
                'purchase_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'image': row['image']
            }
            purchase_history = purchase_history.append(purchase, ignore_index=True)
        purchase_history.to_csv(PURCHASE_HISTORY_CSV, index=False)

        # Empty the cart CSV after checkout
        open(CART_CSV, 'w').close()
        return True
    return False

def generate_product_id():
    products = read_products()
    if products.empty:
        return 1  # Start from 1 if no products exist
    else:
        return products['id'].max() + 1  # Increment the maximum ID by 1

# Sidebar for navigation using radio buttons
st.sidebar.title("Navigation")
option = st.sidebar.radio(
    "Select a page", 
    ("Home", "Add Product", "Cart", "Purchase History", "Categories")
)

if option == "Home":
    st.title("Product Catalog")
    products = read_products()

    for index, row in products.iterrows():
        try:
            st.subheader(row['name'])
            st.write(f"Brand: {row['brand']}")
            st.write(f"Description: {row['description']}")
            st.write(f"Price: ${row['price']}")
            st.write(f"Stock: {row['stock']}")
            st.write(f"Release Date: {row['release_date']}")
            st.image(base64.b64decode(row['image']), use_column_width=True)
            
            # Specify quantity to purchase
            quantity = st.number_input(f"Quantity for {row['name']}", min_value=1, max_value=row['stock'], value=1)

            # Add to Cart button
            if st.button(f"Add to Cart: {row['name']}"):
                if row['stock'] > 0:
                    product_to_cart = {
                        'id': row['id'],
                        'name': row['name'],
                        'brand': row['brand'],
                        'price': row['price'],
                        'quantity': quantity,
                        'image': row['image']
                    }
                    add_to_cart(product_to_cart)
                    st.success(f"Added {quantity} of {row['name']} to the cart.")
                else:
                    st.error("Product out of stock!")
        except KeyError as e:
            st.error(f"KeyError: {e}")

elif option == "Add Product":
    st.title("Add New Product")
    with st.form(key='add_product_form'):
        name = st.text_input("Product Name")
        brand = st.text_input("Brand")
        description = st.text_area("Description")
        price = st.number_input("Price", min_value=0.0)
        category = st.selectbox("Category", ("Laptops", "Headphones", "Mobile", "Electronics", "Fashion", "Toys"))
        stock = st.number_input("Stock Quantity", min_value=0)
        release_date = st.date_input("Release Date", datetime.today())
        image_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
        available = st.checkbox("Available")

        submit_button = st.form_submit_button("Add Product")

        if submit_button:
            if image_file is not None:
                image_bytes = base64.b64encode(image_file.read()).decode()

                # Generate a unique product ID
                new_product_id = generate_product_id()

                new_product = {
                    'id': new_product_id,
                    'name': name,
                    'brand': brand,
                    'description': description,
                    'price': price,
                    'category': category,
                    'stock': stock,
                    'release_date': release_date,
                    'image': image_bytes,
                    'available': available
                }
                add_product(new_product)
                st.success(f"Product {name} added successfully with ID {new_product_id}!")

elif option == "Cart":
    st.title("Shopping Cart")
    cart = read_cart()
    if cart.empty:
        st.write("Your cart is empty.")
    else:
        for index, row in cart.iterrows():
            st.subheader(row['name'])
            st.write(f"Brand: {row['brand']}")
            st.write(f"Price: ${row['price']}")
            st.write(f"Quantity: {row['quantity']}")
            st.image(base64.b64decode(row['image']), use_column_width=True)

            # Remove button for each product
            remove_button = st.button(f"Remove {row['name']} from Cart", key=row['id'])
            if remove_button:
                remove_from_cart(row['id'])
                st.success(f"Removed {row['name']} from the cart.")
                # Refresh the cart data
                cart = read_cart()  

        if st.button("Checkout"):
            if checkout():
                st.success("Checkout successful! Thank you for your purchase.")
            else:
                st.error("Checkout failed.")

elif option == "Purchase History":
    st.title("Purchase History")
    purchase_history = read_purchase_history()
    if purchase_history.empty:
        st.write("No purchase history found.")
    else:
        for index, row in purchase_history.iterrows():
            st.subheader(row['name'])
            st.write(f"Brand: {row['brand']}")
            st.write(f"Price: ${row['price']}")
            st.write(f"Quantity: {row['quantity']}")
            st.write(f"Purchased on: {row['purchase_date']}")
            st.image(base64.b64decode(row['image']), use_column_width=True)

elif option == "Categories":
    st.title("Categories")
    products = read_products()

    if products.empty:
        st.write("No products available.")
    else:
        categories = products['category'].unique()
        
        if len(categories) == 0:
            st.write("No categories available.")
        else:
            for category in categories:
                st.subheader(category)
                category_products = products[products['category'] == category]
                
                if category_products.empty:
                    st.write("No products available in this category.")
                else:
                    for index, row in category_products.iterrows():
                        st.write(f"**{row['name']}**")
                        st.write(f"Brand: {row['brand']}")
                        st.write(f"Price: ${row['price']}")
                        st.image(base64.b64decode(row['image']), use_column_width=True)
