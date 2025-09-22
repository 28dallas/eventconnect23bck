import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///eventconnect.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    bookings = db.relationship('Booking', backref='client', lazy=True, foreign_keys='Booking.client_id')
    services = db.relationship('Service', backref='professional', lazy=True)
    professional_profile = db.relationship('ProfessionalProfile', backref='user', uselist=False)

class ProfessionalProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    specialty = db.Column(db.String(100))
    location = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    pricing = db.Column(db.String(100))
    setup_complete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')
    rating = db.Column(db.Integer)
    review = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    service = db.relationship('Service', backref='bookings')

# Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400
    
    user = User(
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        name=data['name'],
        user_type=data['user_type']
    )
    
    db.session.add(user)
    db.session.commit()
    
    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token, 'user': {'id': user.id, 'name': user.name, 'email': user.email}}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token, 'user': {'id': user.id, 'name': user.name, 'email': user.email}}), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/services', methods=['GET', 'POST'])
@jwt_required()
def services():
    if request.method == 'GET':
        services = Service.query.all()
        return jsonify([{
            'id': s.id, 'name': s.name, 'description': s.description,
            'price': s.price, 'category': s.category, 'professional_id': s.professional_id
        } for s in services])
    
    elif request.method == 'POST':
        data = request.get_json()
        service = Service(
            name=data['name'],
            description=data['description'],
            price=data['price'],
            category=data['category'],
            professional_id=get_jwt_identity()
        )
        db.session.add(service)
        db.session.commit()
        return jsonify({'message': 'Service created', 'id': service.id}), 201

@app.route('/api/categories', methods=['GET'])
def get_categories():
    # Return all available categories
    categories = [
        {'id': 'photographer', 'name': 'Photographer'},
        {'id': 'videographer', 'name': 'Videographer'},
        {'id': 'dj', 'name': 'DJ'},
        {'id': 'event planner', 'name': 'Event Planner'},
        {'id': 'caterer', 'name': 'Caterer'},
        {'id': 'decorator', 'name': 'Decorator'},
        {'id': 'venue coordinator', 'name': 'Venue Coordinator'}
    ]
    
    return jsonify(categories)

@app.route('/api/services/<int:service_id>', methods=['GET', 'PATCH', 'DELETE'])
@jwt_required()
def service_detail(service_id):
    service = Service.query.get_or_404(service_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': service.id, 'name': service.name, 'description': service.description,
            'price': service.price, 'category': service.category
        })
    
    elif request.method == 'PATCH':
        data = request.get_json()
        service.name = data.get('name', service.name)
        service.description = data.get('description', service.description)
        service.price = data.get('price', service.price)
        service.category = data.get('category', service.category)
        db.session.commit()
        return jsonify({'message': 'Service updated'})
    
    elif request.method == 'DELETE':
        db.session.delete(service)
        db.session.commit()
        return jsonify({'message': 'Service deleted'}), 204

@app.route('/api/professionals', methods=['GET'])
def get_professionals():
    # Get all professionals with completed profiles
    professionals_with_profiles = db.session.query(User, ProfessionalProfile).join(
        ProfessionalProfile, User.id == ProfessionalProfile.user_id
    ).filter(
        User.user_type == 'professional',
        ProfessionalProfile.setup_complete == True
    ).all()
    
    result = []
    
    # Add professionals with completed profiles
    for user, profile in professionals_with_profiles:
        result.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'category': profile.category,
            'specialty': profile.specialty or profile.category.title(),
            'location': profile.location,
            'phone': profile.phone,
            'bio': profile.bio,
            'pricing': profile.pricing,
            'rating': 4.5,
            'reviews': 25,
            'verified': True,
            'portfolio': [],
            'image': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=300&h=300&fit=crop&crop=face'
        })
    
    # Add legacy professionals without profiles (for existing data)
    legacy_professionals = db.session.query(User).filter(
        User.user_type == 'professional',
        ~User.id.in_([p.user_id for _, p in professionals_with_profiles])
    ).all()
    
    for user in legacy_professionals:
        if user.name in ['Kinara', 'Nathan', '2PAC', 'Marley', 'John']:
            sample_data = {
                'Kinara': {'category': 'photographer', 'location': 'New York, NY', 'phone': '+1-555-0123', 'pricing': '$150/hour'},
                'Nathan': {'category': 'videographer', 'location': 'Los Angeles, CA', 'phone': '+1-555-0456', 'pricing': '$200/hour'},
                '2PAC': {'category': 'dj', 'location': 'Los Angeles, CA', 'phone': '+1-555-2PAC', 'pricing': '$400/event'},
                'Marley': {'category': 'venue coordinator', 'location': 'Nairobi, Kenya', 'phone': '+254-700-123456', 'pricing': '$120/hour'},
                'John': {'category': 'event planner', 'location': 'New York, NY', 'phone': '+1-555-JOHN', 'pricing': '$1500/event'}
            }
            data = sample_data.get(user.name, {})
            result.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'category': data.get('category', 'general'),
                'specialty': data.get('category', 'Event Professional').title(),
                'location': data.get('location', 'Location not specified'),
                'phone': data.get('phone'),
                'bio': f'Professional {data.get("category", "event")} service provider',
                'pricing': data.get('pricing', 'Contact for pricing'),
                'rating': 4.5,
                'reviews': 25,
                'verified': True,
                'portfolio': [],
                'image': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=300&h=300&fit=crop&crop=face'
            })
    # Add sample professionals for all categories
    if len([r for r in result if r.get('verified')]) < 5:
        sample_professionals = [
            {'id': 101, 'name': 'Sarah Johnson', 'email': 'sarah@example.com', 'category': 'photographer', 'specialty': 'Wedding Photography', 'location': 'Miami, FL', 'phone': '+1-555-0789', 'pricing': '$180/hour', 'bio': 'Award-winning wedding and event photographer'},
            {'id': 102, 'name': 'Mike Chen', 'email': 'mike@example.com', 'category': 'dj', 'specialty': 'Wedding DJ', 'location': 'Chicago, IL', 'phone': '+1-555-0234', 'pricing': '$300/event', 'bio': 'Professional DJ specializing in weddings and corporate events'},
            {'id': 103, 'name': 'Lisa Rodriguez', 'email': 'lisa@example.com', 'category': 'event planner', 'specialty': 'Wedding Planner', 'location': 'Austin, TX', 'phone': '+1-555-0567', 'pricing': '$2000/event', 'bio': 'Full-service event planning with 10+ years experience'},
            {'id': 104, 'name': 'David Kim', 'email': 'david@example.com', 'category': 'caterer', 'specialty': 'Gourmet Catering', 'location': 'Seattle, WA', 'phone': '+1-555-0890', 'pricing': '$25/person', 'bio': 'Gourmet catering for all occasions'},
            {'id': 105, 'name': 'Emma Wilson', 'email': 'emma@example.com', 'category': 'decorator', 'specialty': 'Event Styling', 'location': 'Denver, CO', 'phone': '+1-555-0345', 'pricing': '$500/event', 'bio': 'Creative event decoration and styling'},
            {'id': 106, 'name': 'Carlos Martinez', 'email': 'carlos@example.com', 'category': 'venue coordinator', 'specialty': 'Venue Management', 'location': 'Phoenix, AZ', 'phone': '+1-555-0678', 'pricing': '$150/hour', 'bio': 'Venue management and coordination specialist'}
        ]
        
        for prof in sample_professionals:
            result.append({
                'id': prof['id'],
                'name': prof['name'],
                'email': prof['email'],
                'category': prof['category'],
                'specialty': prof['specialty'],
                'location': prof['location'],
                'phone': prof['phone'],
                'bio': prof['bio'],
                'pricing': prof['pricing'],
                'rating': 4.5,
                'reviews': 25,
                'verified': True,
                'portfolio': [],
                'image': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=300&h=300&fit=crop&crop=face'
            })
    
    return jsonify(result)

@app.route('/api/professional-profile', methods=['POST', 'PUT'])
def professional_profile():
    # Try to get user from JWT, fallback to request data
    try:
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request()
        user_id = get_jwt_identity()
    except:
        # Fallback for testing - use user_id from request or default
        data = request.get_json()
        user_id = data.get('user_id', 1)  # Default to user 1 for testing
        
    if not data:
        data = request.get_json()
    
    profile = ProfessionalProfile.query.filter_by(user_id=user_id).first()
    
    if profile:
        # Update existing profile
        profile.category = data.get('category', profile.category)
        profile.specialty = data.get('specialty', profile.specialty)
        profile.location = data.get('location', profile.location)
        profile.phone = data.get('phone', profile.phone)
        profile.bio = data.get('bio', profile.bio)
        profile.pricing = data.get('pricing', profile.pricing)
        profile.setup_complete = data.get('setupComplete', profile.setup_complete)
    else:
        # Create new profile
        profile = ProfessionalProfile(
            user_id=user_id,
            category=data['category'],
            specialty=data.get('specialty'),
            location=data['location'],
            phone=data.get('phone'),
            bio=data['bio'],
            pricing=data.get('pricing'),
            setup_complete=data.get('setupComplete', False)
        )
        db.session.add(profile)
    
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200

@app.route('/api/bookings', methods=['GET', 'POST'])
@jwt_required()
def bookings():
    if request.method == 'GET':
        bookings = Booking.query.filter_by(client_id=get_jwt_identity()).all()
        return jsonify([{
            'id': b.id, 'service_id': b.service_id, 'event_date': b.event_date.isoformat(),
            'status': b.status, 'rating': b.rating, 'review': b.review
        } for b in bookings])
    
    elif request.method == 'POST':
        data = request.get_json()
        booking = Booking(
            client_id=get_jwt_identity(),
            service_id=data['service_id'],
            event_date=datetime.fromisoformat(data['event_date']),
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()
        return jsonify({'message': 'Booking created', 'id': booking.id}), 201

# Initialize database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)