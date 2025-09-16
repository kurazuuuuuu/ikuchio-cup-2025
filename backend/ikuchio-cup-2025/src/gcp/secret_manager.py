from google.cloud import secretmanager

class SecretManagerUtil: #GCPのシークレット取得
    def get_secret(self, project_id: str, secret_id: str) -> str:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")

if __name__ == '__main__':
    SecretManagerUtil().get_secret("88236233617", "google-vertexai-api-key")