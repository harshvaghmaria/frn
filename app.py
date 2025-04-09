import os
import psycopg2
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_file 

from werkzeug.utils import secure_filename
from psycopg2 import sql

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for flash messages
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database Connection Function
def db_conn():
    return psycopg2.connect(database="FERONIA", user="postgres", password="root", host="localhost", port="5432")

# Home Page - Display Items
@app.route('/')
def index():
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM frn")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', data=data)

# Create New Item (Manual Entry)
@app.route('/create', methods=['POST'])
def create():
    conn = db_conn()
    cur = conn.cursor()
    
    name = request.form['name']
    style = request.form['style']
    mfg = request.form['mfg']
    ct = request.form['ct']
    price = request.form['price']
    type = request.form['type']
    subtype = request.form['subtype']
    shape = request.form['shape']
    size = request.form['size']
    image1 = request.form['image1']
    image2 = request.form['image2']
    image3 = request.form['image3']
    image4 = request.form['image4']
    image5 = request.form['image5']
    image6 = request.form['image6']

    cur.execute("""
        INSERT INTO frn (name, style, mfg, ct, price, type, subtype, shape, size, image1, image2, image3, image4, image5, image6)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (name, style, mfg, ct, price, type, subtype, shape, size, image1, image2, image3, image4, image5, image6))
    
    conn.commit()
    cur.close()
    conn.close()
    
    flash("Item added successfully!", "success")
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    conn = db_conn()
    cur = conn.cursor()

    if request.method == 'GET':
        # Fetch the existing item for the given ID
        cur.execute("SELECT * FROM frn WHERE id = %s", (id,))
        item = cur.fetchone()
        cur.close()
        conn.close()

        if not item:
            return "Item not found", 404

        return render_template('update.html', item=item)

    elif request.method == 'POST':
        # Process the update form submission
        name = request.form['name']
        style = request.form['style']
        mfg = request.form['mfg']
        ct = request.form['ct']
        price = request.form['price']
        type = request.form['type']
        subtype = request.form['subtype']
        shape = request.form['shape']
        size = request.form['size']
        image1 = request.form['image1']
        image2 = request.form['image2']
        image3 = request.form['image3']
        image4 = request.form['image4']
        image5 = request.form['image5']
        image6 = request.form['image6']

        cur.execute("""
            UPDATE frn SET name = %s, style = %s, mfg = %s, ct = %s, price = %s, type = %s, subtype = %s,
            shape = %s, size = %s, image1 = %s, image2 = %s, image3 = %s, image4 = %s, image5 = %s, image6 = %s
            WHERE id = %s
        """, (name, style, mfg, ct, price, type, subtype, shape, size, image1, image2, image3, image4, image5, image6, id))

        conn.commit()
        cur.close()
        conn.close()

        flash("Item updated successfully!", "success")

        # Redirect to index (home page) after successful update
        return redirect(url_for('index'))


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for('index'))

    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Process the Excel file
        try:
            df = pd.read_excel(filepath)

            # Ensure required columns exist in the uploaded file
            required_columns = ['name', 'style', 'mfg', 'ct', 'price', 'type', 'subtype', 'shape', 'size']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                flash(f"Missing columns: {', '.join(missing_columns)}", "danger")
                return redirect(url_for('index'))

            conn = db_conn()
            cur = conn.cursor()

            for _, row in df.iterrows():
                # Handle missing optional fields
                images = [row.get(f'image{i}', None) for i in range(1, 7)]

                # Convert decimal fields to proper types
                try:
                    ct = float(row['ct']) if pd.notna(row['ct']) else 0.0
                    price = float(row['price']) if pd.notna(row['price']) else 0.0
                except ValueError:
                    flash("Invalid number format in 'ct' or 'price' column.", "danger")
                    return redirect(url_for('index'))

                # Insert into the database
                cur.execute("""
                    INSERT INTO frn (name, style, mfg, ct, price, type, subtype, shape, size, image1, image2, image3, image4, image5, image6)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (row['name'], row['style'], row['mfg'], ct, price, row['type'], row['subtype'], row['shape'], row['size'], *images))

            conn.commit()
            cur.close()
            conn.close()

            flash("File uploaded and data inserted successfully!", "success")
        except Exception as e:
            flash(f"Error processing file: {e}", "danger")

        return redirect(url_for('index'))

    flash("Invalid file format. Only .xlsx files are allowed.", "danger")
    return redirect(url_for('index'))



# Delete Item
@app.route('/delete', methods=['POST'])
def delete():
    conn = db_conn()
    cur = conn.cursor()
    id = request.form['id']
    cur.execute("DELETE FROM frn WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    
    flash("Item deleted successfully!", "success")
    return redirect(url_for('index'))


@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for('index'))

    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        try:
            # Read the uploaded Excel file
            df = pd.read_excel(filepath)

            # Verify required columns
            required_columns = ['name', 'style', 'mfg', 'ct', 'price', 'type', 'subtype', 'shape', 'size']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                flash(f"Missing columns: {', '.join(missing_columns)}", "danger")
                return redirect(url_for('index'))

            # Fill missing values with default values
            df.fillna({
                'name': 'Unknown',
                'style': 'Unknown',
                'mfg': 'Unknown',
                'ct': 0.0,
                'price': 0.0,
                'type': 'Unknown',
                'subtype': 'Unknown',
                'shape': 'Unknown',
                'size': 'Unknown'
            }, inplace=True)

            # Save the updated file
            updated_filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"updated_{filename}")
            df.to_excel(updated_filepath, index=False)

            # Provide the updated file for download
            return send_file(updated_filepath, as_attachment=True)

        except Exception as e:
            flash(f"Error processing file: {e}", "danger")
            return redirect(url_for('index'))

    flash("Invalid file format. Only .xlsx files are allowed.", "danger")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)