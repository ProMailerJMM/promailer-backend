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
@app.route('/stripe-key', methods=['GET'])
def get_stripe_key():
    # Dynamically serve the exact publishable key configured in your Render dashboard env variables
    pub_key = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    return jsonify({'publishableKey': pub_key}), 200


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
        # Safe query parameter parsing
        args = request.args or {}
        payment_intent_id = args.get('payment_intent_id')
        platform = args.get('platform')

        print(f"[Payment Server] Download request received. ID: {payment_intent_id}, Platform: {platform}")

        if not payment_intent_id or not platform:
            return 'Missing required download parameters', 400

        if platform not in PLATFORM_FILES:
            return 'Invalid platform selected', 400

        # Retrieve PaymentIntent details from Stripe
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        except Exception as stripe_err:
            print(f"[Payment Server] Stripe retrieve failed: {stripe_err}")
            return f"Stripe retrieval failed: {str(stripe_err)}", 400

        # Safe status and metadata checks
        status = getattr(intent, 'status', None) or intent.get('status')
        
        # Safely extract metadata regardless of Stripe SDK version (handles dict, StripeObject, or None)
        metadata = {}
        intent_metadata = getattr(intent, 'metadata', None) or intent.get('metadata')
        if intent_metadata:
            if hasattr(intent_metadata, 'get'):
                metadata = intent_metadata
            elif isinstance(intent_metadata, dict):
                metadata = intent_metadata
            else:
                try:
                    metadata = dict(intent_metadata)
                except Exception:
                    pass

        platform_meta = None
        if hasattr(metadata, 'get'):
            platform_meta = metadata.get('platform')
        elif isinstance(metadata, dict):
            platform_meta = metadata.get('platform')
        
        # Double check dictionary fallback
        if not platform_meta:
            try:
                platform_meta = intent['metadata']['platform']
            except Exception:
                pass

        print(f"[Payment Server] Verification - Status: {status}, Metadata Platform: {platform_meta}, Target: {platform}")

        # Secure verification: confirm success status and metadata parameters
        if status == 'succeeded' and platform_meta == platform:
            file_path = PLATFORM_FILES[platform]
            if os.path.exists(file_path):
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=os.path.basename(file_path)
                )
            else:
                print(f"[Payment Server] File not found: {file_path}")
                return 'Requested release package not found on server', 404
        else:
            print(f"[Payment Server] Verification failed. Status: {status}, Meta: {platform_meta}")
            return 'Payment verification failed', 403

    except Exception as e:
        import traceback
        print(f"[Payment Server] Error verifying download:")
        traceback.print_exc()
        return f"Server Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
