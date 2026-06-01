import os
import stripe
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv

# Load local environment parameters
load_dotenv()

app = Flask(__name__)
# Enable CORS for frontend API communications (e.g., Netlify -> Render)
CORS(app)

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

PLATFORM_FILES = {
    'mac': 'files/ProMailer-Mac.zip',
    'windows': 'files/ProMailer-Windows.zip',
    'linux': 'files/ProMailer-Linux.zip'
}

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'status': 'active',
        'gateway': 'ProMailer Payment & Release Delivery Service',
        'secure': True
    }), 200

@app.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    try:
        data = request.json or {}
        platform = data.get('platform')
        email = data.get('email')

        if not platform or platform not in PLATFORM_FILES:
            return jsonify({'error': 'Invalid platform selected'}), 400
        
        if not email:
            return jsonify({'error': 'Email address is required'}), 400

        # Create Stripe PaymentIntent with platform and email metadata
        intent = stripe.PaymentIntent.create(
            amount=2900,  # $29.00 USD
            currency='usd',
            payment_method_types=['card'],
            metadata={
                'platform': platform,
                'email': email
            },
            receipt_email=email
        )

        return jsonify({
            'clientSecret': intent.client_secret,
            'paymentIntentId': intent.id
        })

    except Exception as e:
        print(f"[Payment Server] Error creating intent: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['GET'])
def download():
    try:
        payment_intent_id = request.args.get('payment_intent_id')
        platform = request.args.get('platform')

        if not payment_intent_id or not platform:
            return 'Missing required download parameters', 400

        if platform not in PLATFORM_FILES:
            return 'Invalid platform selected', 400

        # Retrieve PaymentIntent details from Stripe
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        # Secure verification: confirm success status and metadata parameters
        if intent.status == 'succeeded' and intent.metadata.get('platform') == platform:
            file_path = PLATFORM_FILES[platform]
            if os.path.exists(file_path):
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=os.path.basename(file_path)
                )
            else:
                return 'Requested release package not found on server', 404
        else:
            return 'Payment verification failed', 403

    except Exception as e:
        print(f"[Payment Server] Error verifying download: {e}")
        return f"Server Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
