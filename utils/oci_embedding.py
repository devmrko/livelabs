import oci
import os
import logging
from typing import List

# --- 기본 로깅 설정 / Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 설정 상수 / Configuration Constants ---
# OCI 생성형 AI 추론 서비스 엔드포인트 (시카고 리전)
# OCI Generative AI Inference service endpoint (Chicago region)
ENDPOINT = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"

# 사용할 Cohere 임베딩 모델 ID
# Cohere embedding model ID to use
#MODEL_ID = "cohere.embed-english-v3.0"  # 영어 전용 모델 / English-only model
MODEL_ID = "cohere.embed-v4.0"  # 다국어 지원 모델 / Multilingual model

def init_client(config: dict) -> oci.generative_ai_inference.GenerativeAiInferenceClient:
    """OCI 생성형 AI 추론 클라이언트를 초기화하고 반환합니다.
    Initializes and returns the OCI Generative AI Inference Client."""
    logging.info(f"엔드포인트 클라이언트 초기화 / Initializing client for endpoint: {ENDPOINT}")
    return oci.generative_ai_inference.GenerativeAiInferenceClient(
        config=config,  # OCI 설정 정보 / OCI configuration
        service_endpoint=ENDPOINT,  # 서비스 엔드포인트 / Service endpoint
        retry_strategy=oci.retry.NoneRetryStrategy(),  # 재시도 전략 없음 / No retry strategy
        timeout=(10, 240)  # 연결 및 읽기 타임아웃 (초) / Connection and read timeout (seconds)
    )

def get_embeddings(client: oci.generative_ai_inference.GenerativeAiInferenceClient, compartment_id: str, texts: List[str]) -> List[List[float]]:
    """
    지정된 클라이언트를 사용하여 텍스트 목록에 대한 임베딩을 생성하고 반환합니다.
    Generates and returns embeddings for a list of texts using the specified client.
    """
    logging.info(f"모델 '{MODEL_ID}'를 사용하여 {len(texts)}개 텍스트에 대한 임베딩 요청")
    logging.info(f"Requesting embeddings for {len(texts)} text(s) using model '{MODEL_ID}'.")
    try:
        # 임베딩 요청 세부사항 구성 / Configure embedding request details
        embed_details = oci.generative_ai_inference.models.EmbedTextDetails(
            inputs=texts,  # 임베딩할 텍스트 목록 / List of texts to embed
            serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(model_id=MODEL_ID),  # 온디맨드 서빙 모드 / On-demand serving mode
            compartment_id=compartment_id,  # OCI 구획 ID / OCI compartment ID
            truncate="END"  # 텍스트가 너무 길면 끝에서 자르기 / Truncate from end if text is too long
        )
        
        # OCI 서비스에 임베딩 요청 / Request embeddings from OCI service
        response = client.embed_text(embed_details)
        logging.info("OCI 서비스로부터 임베딩을 성공적으로 수신했습니다.")
        logging.info("Successfully received embeddings from OCI service.")
        return response.data.embeddings  # type: ignore

    except oci.exceptions.ServiceError as e:
        logging.error(f"임베딩 중 OCI 서비스 오류 / OCI Service Error during embedding: Status {e.status} - {e.message}", exc_info=True)
        return []
    except Exception as e:
        logging.error(f"임베딩 중 예상치 못한 오류 발생 / An unexpected error occurred during embedding: {e}", exc_info=True)
        return []

def main():
    """임베딩 테스트를 실행하는 메인 함수.
    Main function to execute the embedding test."""
    try:
        # OCI 설정 파일에서 구성 로드 (~/.oci/config)
        # Load configuration from OCI config file (~/.oci/config)
        config = oci.config.from_file()
        compartment_id = config.get("tenancy")  # 테넌시 ID를 구획 ID로 사용 / Use tenancy ID as compartment ID
        
        if not compartment_id:
            logging.error("구획 ID를 로드할 수 없습니다. ~/.oci/config 파일에 'tenancy' 키가 설정되어 있는지 확인하세요.")
            logging.error("Compartment ID could not be loaded. Ensure the 'tenancy' key is set in your ~/.oci/config file.")
            return

        # OCI 클라이언트 초기화 / Initialize OCI client
        client = init_client(config)
        
        # 임베딩할 테스트 텍스트들 / Test texts to embed
        texts_to_embed = [
            "The quick brown fox jumps over the lazy dog.",  # 영어 테스트 텍스트 / English test text
            "Exploring the capabilities of Large Language Models.",  # LLM 관련 텍스트 / LLM-related text
            "Oracle Cloud Infrastructure provides powerful AI services."  # OCI AI 서비스 관련 텍스트 / OCI AI services text
        ]
        
        # 임베딩 생성 요청 / Request embedding generation
        embeddings = get_embeddings(client, compartment_id, texts_to_embed)
        
        # 결과 출력 / Output results
        if embeddings:
            logging.info("--- 결과 / RESULTS ---")
            logging.info(f"성공적으로 {len(embeddings)}개의 임베딩을 생성했습니다.")
            logging.info(f"Successfully generated {len(embeddings)} embeddings.")
            logging.info(f"각 벡터의 차원 / Dimension of each vector: {len(embeddings[0])}")
            logging.info(f"첫 번째 벡터의 처음 5개 값 / First 5 values of the first vector: {embeddings[0][:5]}")
        else:
            logging.error("임베딩 생성에 실패했습니다. / Failed to generate embeddings.")

    except oci.exceptions.ConfigFileNotFound:
        logging.error("'~/.oci/config'에서 OCI 설정 파일을 찾을 수 없습니다. 올바르게 설정되어 있는지 확인하세요.")
        logging.error("OCI config file not found at '~/.oci/config'. Please ensure it is set up correctly.")
    except Exception as e:
        logging.error(f"설정 중 예상치 못한 오류 발생 / An unexpected error occurred during setup: {e}", exc_info=True)

if __name__ == "__main__":
    # 스크립트가 직접 실행될 때 메인 함수 호출
    # Call main function when script is run directly
    main() 