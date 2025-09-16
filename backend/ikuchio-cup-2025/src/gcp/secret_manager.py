from google.cloud import secretmanager

class SecretManagerUtil: #GCPのシークレット取得
    def get_secret(self, project_id: str, secret_id: str) -> str:
        try:
            print(f"[SecretManager Debug] Creating client...")
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
            print(f"[SecretManager Debug] Accessing secret: {name}")
            response = client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8")
            print(f"[SecretManager Debug] Secret retrieved successfully")
            return secret_value
        except Exception as e:
            print(f"[SecretManager Debug] Error: {type(e).__name__}: {str(e)}")
            raise e

if __name__ == '__main__':
    SecretManagerUtil().get_secret("88236233617", "google-vertexai-api-key")