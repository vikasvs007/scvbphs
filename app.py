from flask import Flask, render_template, request, flash, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, AdmissionEnquiry, Admin
import os
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
from functools import wraps

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///school.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# Create admin-only decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Admin Profile Management
@app.route('/admin/profile', methods=['GET', 'POST'])
@admin_required
def admin_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Verify current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('admin_profile'))

        # Check if new password matches confirmation
        if new_password and new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('admin_profile'))

        try:
            # Update username if changed
            if username != current_user.username:
                if Admin.query.filter_by(username=username).first():
                    flash('Username already exists', 'error')
                    return redirect(url_for('admin_profile'))
                current_user.username = username

            # Update email if changed
            if email != current_user.email:
                try:
                    valid = validate_email(email)
                    email = valid.email
                    if Admin.query.filter_by(email=email).first():
                        flash('Email already exists', 'error')
                        return redirect(url_for('admin_profile'))
                    current_user.email = email
                except EmailNotValidError:
                    flash('Invalid email address', 'error')
                    return redirect(url_for('admin_profile'))

            # Update password if provided
            if new_password:
                current_user.set_password(new_password)

            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('admin_profile'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating profile', 'error')
            return redirect(url_for('admin_profile'))

    return render_template('admin/profile.html')

# Create Initial Admin Account
@app.route('/setup-admin', methods=['GET', 'POST'])
def setup_admin():
    # Check if any admin account exists
    if Admin.query.first() is not None:
        flash('Admin account already exists', 'error')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'error')
            return redirect(url_for('setup_admin'))

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('setup_admin'))

        try:
            # Validate email
            valid = validate_email(email)
            email = valid.email

            # Create admin account
            admin = Admin(username=username, email=email)
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()

            flash('Admin account created successfully. Please login.', 'success')
            return redirect(url_for('admin_login'))

        except EmailNotValidError:
            flash('Invalid email address', 'error')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating admin account', 'error')

    return render_template('admin/setup.html')

# Create database tables
with app.app_context():
    db.create_all()
    # Create default admin if not exists
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin', email='admin@schoolofindia.edu')
        admin.set_password('admin123')  # Change this password in production!
        db.session.add(admin)
        db.session.commit()

# Admin authentication routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('view_enquiries'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin)
            admin.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('view_enquiries'))
        
        flash('Invalid username or password', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('admin_login'))

# Main routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/admissions', methods=['GET'])
def admissions():
    return render_template('admissions.html')

@app.route('/submit-admission', methods=['POST'])
def submit_admission():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            grade = request.form.get('grade')
            grade_interested = request.form.get('grade_interested')

            # Validate required fields
            if not all([name, email, phone, grade, grade_interested]):
                flash('All fields are required', 'error')
                return redirect(url_for('admissions'))

            # Validate email
            try:
                valid = validate_email(email)
                email = valid.email
            except EmailNotValidError:
                flash('Please enter a valid email address', 'error')
                return redirect(url_for('admissions'))

            # Validate phone number (basic validation)
            if not phone.isdigit() or len(phone) < 10:
                flash('Please enter a valid phone number', 'error')
                return redirect(url_for('admissions'))

            # Create new admission enquiry
            new_enquiry = AdmissionEnquiry(
                name=name,
                email=email,
                phone=phone,
                grade=grade,
                grade_interested=grade_interested
            )

            # Save to database
            db.session.add(new_enquiry)
            db.session.commit()

            flash('Thank you for your enquiry! We will contact you soon.', 'success')
            return redirect(url_for('admissions'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('admissions'))

@app.route('/gallery')
def gallery():
    # Get the filter parameter from the URL, default to 'all' if not provided
    filter_type = request.args.get('filter', 'all')
    return render_template('gallery.html', active_filter=filter_type)

@app.route('/transfer-certificate')
def transfer_certificate():
    return render_template('transfer_certificate.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# Admin routes (protected)
@app.route('/admin/enquiries')
@admin_required
def view_enquiries():
    # Get both types of enquiries
    admission_enquiries = AdmissionEnquiry.query.order_by(AdmissionEnquiry.created_at.desc()).all()
    contact_enquiries = Contact.query.order_by(Contact.date_submitted.desc()).all()
    
    # Add type field to each enquiry
    all_enquiries = []
    
    for enquiry in admission_enquiries:
        enquiry_dict = enquiry.to_dict()
        enquiry_dict['type'] = 'admission'
        all_enquiries.append(enquiry_dict)
    
    for enquiry in contact_enquiries:
        enquiry_dict = enquiry.to_dict()
        enquiry_dict['type'] = 'contact'
        all_enquiries.append(enquiry_dict)
    
    # Sort all enquiries by date
    all_enquiries.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('admin/enquiries.html', all_enquiries=all_enquiries)

@app.route('/admin/enquiry/<int:id>')
@admin_required
def get_enquiry(id):
    # Try admission enquiry first
    enquiry = AdmissionEnquiry.query.get(id)
    if enquiry:
        data = enquiry.to_dict()
        data['type'] = 'admission'
        return jsonify(data)
    
    # If not found, try contact enquiry
    enquiry = Contact.query.get(id)
    if enquiry:
        data = enquiry.to_dict()
        data['type'] = 'contact'
        return jsonify(data)
    
    abort(404)

@app.route('/admin/enquiry/<int:id>/status', methods=['POST'])
@admin_required
def update_enquiry_status(id):
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        # Try admission enquiry first
        enquiry = AdmissionEnquiry.query.get(id)
        if enquiry:
            enquiry.status = new_status
            db.session.commit()
            return jsonify({'success': True})
        
        # If not found, try contact enquiry
        enquiry = Contact.query.get(id)
        if enquiry:
            enquiry.status = new_status
            db.session.commit()
            return jsonify({'success': True})
        
        abort(404)
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/enquiry/<int:id>', methods=['DELETE'])
@admin_required
def delete_enquiry(id):
    try:
        # Try admission enquiry first
        enquiry = AdmissionEnquiry.query.get(id)
        if enquiry:
            db.session.delete(enquiry)
            db.session.commit()
            return jsonify({'success': True})
        
        # If not found, try contact enquiry
        enquiry = Contact.query.get(id)
        if enquiry:
            db.session.delete(enquiry)
            db.session.commit()
            return jsonify({'success': True})
        
        abort(404)
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/gallery/<album_name>')
def view_album(album_name):
    # Dictionary mapping album names to their folder paths and details
    albums = {
        'campus': {
            'title': 'Campus Life',
            'description': 'Exploring our beautiful campus and facilities',
            'folder': 'campus',
            'images': ['schoolphoto.jpeg','WhatsApp Image 2025-01-18 at 11.57.16 PM.jpeg',
                       'innovation.jpeg','savithmaa.jpg','WhatsApp Image 2025-01-19 at 12.11.03 AM (1).jpeg',
                       
                       'WhatsApp Image 2025-01-17 at 4.07.35 PM.jpeg',
                       'WhatsApp Image 2025-01-17 at 4.07.07 PM (1).jpeg','WhatsApp Image 2025-01-17 at 4.07.36 PM (1).jpeg',
                       'WhatsApp Image 2025-01-17 at 4.07.38 PM.jpeg','WhatsApp Image 2025-01-19 at 12.11.03 AM.jpeg',
                       'WhatsApp Image 2025-01-19 at 12.22.18 AM.jpeg']
        },
        'events': {
            'title': 'School Events',
            'description': 'Celebrating special moments and achievements',
            'folder': 'events',
            'images': ['envi1.jpeg','prize1.jpeg','innova.jpeg','innovation.jpeg','news.jpeg','news2.jpeg','news3.jpeg',
                       'newz.jpeg','pri.jpeg','prize.jpeg','envi4.jpeg','enviday.jpeg','envimain.jpeg',
                       'raksha.jpeg','sankranti.jpeg','sankranti2.jpeg','parents2.jpeg','parents3.jpeg']
        },
        'activities': {
            'title': 'Student Activities',
            'description': 'Engaging in various educational and extracurricular activities',
            'folder': 'activities',
            'images': ['yoga.jpeg','yoga2.jpeg','yoga3.jpeg','yoga4.jpeg','yoga5.jpeg','yoga7.jpeg','yoga8.jpeg','kannada.jpeg','karate.jpeg','karateimage.jpeg',
                       'pri.jpeg','prize.jpeg','parent.jpeg','parents.jpeg']
        },
        'achievements': {
            'title': 'Student Achievements',
            'description': 'Showcasing our students\' accomplishments and awards',
            'folder': 'achievements',
            'images': ['image.png','kannada.jpeg','achivement.jpeg','pratibha.jpeg',
                       'prixew.jpeg','scienceday.jpeg',
                       'prize1.jpeg','prize.jpeg','vote.jpeg','workshop (2).jpeg','workshop (3).jpeg','workshop3.jpeg',
                       'workshop6.jpeg','prize (2).jpeg','worksop5.jpeg','workshop7.jpeg']
        }
    }
    
    if album_name not in albums:
        abort(404)
        
    album = albums[album_name]
    return render_template('album.html', 
                         album_name=album_name,
                         title=album['title'],
                         description=album['description'],
                         images=album['images'],
                         folder=album['folder'])

@app.route('/staff')
def staff():
    return render_template('staff.html')

# Contact Form Model
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending')  # Pending, Responded, Closed

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.full_name,  # Map full_name to name for consistency
            'email': self.email,
            'phone': self.phone,
            'subject': self.subject,
            'message': self.message,
            'status': self.status,
            'created_at': self.date_submitted.strftime('%Y-%m-%d %H:%M:%S')
        }

@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    if request.method == 'POST':
        new_contact = Contact(
            full_name=request.form['fullName'],
            email=request.form['email'],
            phone=request.form['phone'],
            subject=request.form['subject'],
            message=request.form['message']
        )
        db.session.add(new_contact)
        db.session.commit()
        flash('Thank you for your message. We will get back to you soon!', 'success')
        return redirect(url_for('contact'))

if __name__ == '__main__':
    app.run(debug=True)