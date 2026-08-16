from services.extraction_service import ExtractionService

extractor = ExtractionService(use_bedrock=False)
result = extractor.extract("My Kubernetes pod crashed with OOMKilled. Increased memory from 512Mi to 1Gi.")
print(result)