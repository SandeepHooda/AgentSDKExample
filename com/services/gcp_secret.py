from google.cloud import secretmanager

PROJECT_ID = "digitalpass-sandeep"  # Replace with your GCP project ID


def get_secret_value(secret_id):
    """Fetches a secret from Google Cloud Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    try:
        response = client.access_secret_version(name=name)
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        print(f"Error accessing secret {secret_id}: {e}")
        raise