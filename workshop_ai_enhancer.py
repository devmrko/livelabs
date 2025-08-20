#!/usr/bin/env python3
"""
Workshop AI Enhancer

## 개요 (Abstract)
이 모듈은 Oracle Cloud Infrastructure(OCI) Generative AI를 활용하여 Oracle LiveLabs 워크샵 데이터를 
지능적으로 분석하고 향상시키는 시스템입니다. 원시 워크샵 텍스트 데이터를 입력받아 AI 기반 메타데이터 
추출, 자동 분류, 콘텐츠 강화를 수행한 후 MongoDB에 저장합니다.

### 주요 기능:
- **AI 기반 메타데이터 추출**: 워크샵 제목, 설명, 내용을 분석하여 키워드, 난이도, 카테고리 등을 자동 추출
- **자동 분류 시스템**: 워크샵을 기술 영역별로 분류하고 적절한 리소스 타입 할당
- **배치 처리**: 대량의 워크샵 데이터를 효율적으로 처리하며 진행상황 추적 및 복구 기능 제공
- **이중 저장 구조**: 원본 데이터와 AI 강화된 데이터를 별도 컬렉션에 저장하여 데이터 무결성 보장
- **오류 복구**: AI 처리 실패 시 기본 메타데이터로 폴백하여 데이터 손실 방지

### 사용 사례:
- Oracle LiveLabs 워크샵 콘텐츠의 자동 카탈로그화
- 워크샵 검색 및 추천 시스템을 위한 메타데이터 생성
- 콘텐츠 관리 시스템의 데이터 품질 향상

Enhances workshop data using OCI GenAI and imports to MongoDB collections
Provides AI-powered metadata extraction, categorization, and content enrichment
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Import OCI GenAI utilities
import oci
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference import models as genai_models

from utils.mongo_utils import MongoManager

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkshopAIEnhancer:
    """AI-powered workshop data enhancer using OCI GenAI for metadata extraction"""
    
    def __init__(self):
        self.model_id = "xai.grok-4"
        self.compartment_id = os.getenv('OCI_COMPARTMENT_ID')
        self.endpoint = os.getenv('OCI_GENAI_ENDPOINT')
        self.config_file_path = os.path.expanduser(os.getenv('OCI_CONFIG_PATH', '~/.oci/config'))
        self.config_profile = os.getenv('OCI_CONFIG_PROFILE', 'DEFAULT')
        
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OCI Generative AI client"""
        try:
            oci_config = oci.config.from_file(
                file_location=self.config_file_path,
                profile_name=self.config_profile
            )
            
            if not self.compartment_id and oci_config.get("tenancy"):
                self.compartment_id = oci_config.get("tenancy")
                logger.info(f"Using tenancy ID {self.compartment_id} as compartment ID")
            
            client = GenerativeAiInferenceClient(
                config=oci_config,
                service_endpoint=self.endpoint,
                retry_strategy=oci.retry.NoneRetryStrategy(),
                timeout=(10, 240)
            )
            
            logger.info(f"OCI GenAI client initialized with model: {self.model_id}")
            return client
            
        except Exception as e:
            logger.error(f"Failed to initialize OCI client: {e}")
            return None
    
    def enhance_workshop(self, workshop_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance workshop data using OCI GenAI"""
        
        if not self.client:
            logger.error("OCI client not initialized")
            return workshop_data
        
        try:
            # Prepare workshop information for AI analysis
            workshop_info = f"""
            제목: {workshop_data.get('title', 'N/A')}
            설명: {workshop_data.get('description', 'N/A')}
            텍스트 내용: {workshop_data.get('text_content', '')[:2000]}  # Limit text for prompt
            URL: {workshop_data.get('url', 'N/A')}
            """
            
            enhancement_prompt = f"""
            다음 워크샵 정보를 분석하고 향상된 형태로 변환해주세요:

            {workshop_info}

            다음 JSON 형식으로 응답해주세요:
            {{
                "keywords": ["주요 키워드들"],
                "author": "작성자 또는 기관명",
                "difficulty": "BEGINNER|INTERMEDIATE|ADVANCED",
                "category": "주요 카테고리",
                "duration_estimate": "예상 소요 시간",
                "resource_type": "WORKSHOP|TUTORIAL|GUIDE|DEMO",
                "source": "Oracle LiveLabs",
                "language": "ko|en"
            }}

            분석 기준:
            - keywords: 워크샵 내용에서 추출한 주요 기술 키워드들
            - author: Oracle 또는 관련 기관명
            - difficulty: 내용의 복잡도에 따라 판단
            - category: 주요 기술 영역 (예: OCI, Database, Security, etc.)
            - duration_estimate: 워크샵 제목이나 내용에서 추정
            - resource_type: 워크샵 형태에 따라 판단
            - language: 한국어/영어 등 언어 구분
            """
            
            content = genai_models.TextContent(text=enhancement_prompt, type="TEXT")
            message = genai_models.Message(role="USER", content=[content])
            
            chat_request = genai_models.GenericChatRequest(
                api_format=genai_models.BaseChatRequest.API_FORMAT_GENERIC,
                messages=[message],
                max_tokens=1000,
                temperature=0.3
            )
            
            chat_details = genai_models.ChatDetails(
                serving_mode=genai_models.OnDemandServingMode(model_id=self.model_id),
                chat_request=chat_request,
                compartment_id=self.compartment_id
            )
            
            response = self.client.chat(chat_details)
            enhancement_result = response.data.chat_response.choices[0].message.content[0].text.strip()
            
            # Log the LLM response for debugging
            logger.info(f"LLM Enhancement Response for workshop {workshop_data.get('workshop_id', 'unknown')}:")
            logger.info(f"Response: {enhancement_result[:500]}...")  # Log first 500 chars
            
            # Parse the enhancement result
            try:
                # Extract JSON from response
                if "```json" in enhancement_result:
                    json_start = enhancement_result.find("```json") + 7
                    json_end = enhancement_result.find("```", json_start)
                    json_str = enhancement_result[json_start:json_end].strip()
                else:
                    start = enhancement_result.find("{")
                    end = enhancement_result.rfind("}") + 1
                    json_str = enhancement_result[start:end]
                
                enhancement_data = json.loads(json_str)
                
                # Create enhanced workshop document
                enhanced_workshop = {
                    '_id': workshop_data.get('workshop_id', f"workshop_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                    'id': workshop_data.get('workshop_id', 'unknown'),
                    'title': workshop_data.get('title', ''),
                    'description': workshop_data.get('description', ''),
                    'text_content': workshop_data.get('text_content', ''),
                    'keywords': enhancement_data.get('keywords', []),
                    'author': enhancement_data.get('author', 'Oracle'),
                    'created_at': datetime.now().strftime('%Y-%m-%d'),
                    'difficulty': enhancement_data.get('difficulty', 'INTERMEDIATE'),
                    'category': enhancement_data.get('category', 'General'),
                    'duration_estimate': enhancement_data.get('duration_estimate', 'Unknown'),
                    'resource_type': enhancement_data.get('resource_type', 'WORKSHOP'),
                    'source': enhancement_data.get('source', 'Oracle LiveLabs'),
                    'url': workshop_data.get('url', ''),
                    'language': enhancement_data.get('language', 'ko')
                }
                
                logger.info(f"Enhanced workshop: {workshop_data.get('workshop_id', 'unknown')}")
                return enhanced_workshop
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse enhancement result: {e}")
                # Return original data with basic enhancement
                return self._create_basic_enhancement(workshop_data)
                
        except Exception as e:
            logger.error(f"Error enhancing workshop: {e}")
            return self._create_basic_enhancement(workshop_data)
    
    def _create_basic_enhancement(self, workshop_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic enhancement when AI enhancement fails"""
        return {
            '_id': workshop_data.get('workshop_id', f"workshop_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            'id': workshop_data.get('workshop_id', 'unknown'),
            'title': workshop_data.get('title', ''),
            'description': workshop_data.get('description', ''),
            'text_content': workshop_data.get('text_content', ''),
            'keywords': ['Oracle', 'LiveLabs'],
            'author': 'Oracle',
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'difficulty': 'INTERMEDIATE',
            'category': 'General',
            'duration_estimate': 'Unknown',
            'resource_type': 'WORKSHOP',
            'source': 'Oracle LiveLabs',
            'url': workshop_data.get('url', ''),
            'language': 'ko'
        }

def import_raw_workshop_texts(json_filename="workshop_texts_progress.json", collection_name="workshop_texts"):
    """Import raw workshop text data from JSON file to MongoDB without enhancement"""
    # Load workshop texts from JSON
    try:
        with open(json_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            workshops = data.get("workshops", [])
    except Exception as e:
        logger.error(f"Failed to load {json_filename}: {e}")
        return False

    if not workshops:
        logger.error(f"No workshop texts found in {json_filename}")
        return False

    # Create MongoDB manager
    mongo_manager = MongoManager(collection_name=collection_name)

    # Insert only successful workshop texts
    successful_workshops = [w for w in workshops if w.get("success")]
    logger.info(f"Importing {len(successful_workshops)} successful workshop texts to MongoDB...")

    success = mongo_manager.insert_workshops(successful_workshops)
    if success:
        logger.info(f"Successfully imported {len(successful_workshops)} workshop texts to MongoDB")
    else:
        logger.error("Failed to import workshop texts to MongoDB")

    mongo_manager.close()
    return success

def import_ai_enhanced_workshops(json_filename="workshop_texts_progress.json", collection_name="livelabs_workshops_json2"):
    """Import AI-enhanced workshop data to MongoDB with metadata extraction and categorization"""
    # Load workshop texts from JSON
    try:
        with open(json_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            workshops = data.get("workshops", [])
    except Exception as e:
        logger.error(f"Failed to load {json_filename}: {e}")
        return False

    if not workshops:
        logger.error(f"No workshop texts found in {json_filename}")
        return False

    # Create MongoDB manager for enhanced collection
    mongo_manager = MongoManager(collection_name=collection_name)
    
    # Create AI enhancer
    enhancer = WorkshopAIEnhancer()

    # Process only successful workshop texts
    successful_workshops = [w for w in workshops if w.get("success")]
    logger.info(f"Enhancing and importing {len(successful_workshops)} workshop texts to MongoDB...")

    # Load progress from file if exists
    progress_file = "enhancement_progress.json"
    processed_ids = set()
    
    try:
        if os.path.exists(progress_file):
            with open(progress_file, "r") as f:
                progress_data = json.load(f)
                processed_ids = set(progress_data.get("processed_ids", []))
                logger.info(f"📋 Resuming from progress file. Already processed: {len(processed_ids)} workshops")
    except Exception as e:
        logger.warning(f"Could not load progress file: {e}")

    # Track progress
    processed_count = len(processed_ids)
    failed_count = 0
    
    for i, workshop in enumerate(successful_workshops, 1):
        workshop_id = workshop.get('workshop_id', 'unknown')
        
        # Skip if already processed
        if workshop_id in processed_ids:
            logger.info(f"⏭️  Skipping already processed workshop {workshop_id}")
            continue
            
        logger.info(f"Processing workshop {i}/{len(successful_workshops)}: {workshop_id}")
        
        try:
            # Enhance workshop using AI
            enhanced_workshop = enhancer.enhance_workshop(workshop)
            
            # Insert single workshop immediately
            success = mongo_manager.insert_single_workshop(enhanced_workshop)
            
            if success:
                processed_count += 1
                processed_ids.add(workshop_id)
                logger.info(f"✅ Successfully processed and committed workshop {workshop_id} ({processed_count}/{len(successful_workshops)})")
                
                # Save progress every 10 workshops
                if processed_count % 10 == 0:
                    with open(progress_file, "w") as f:
                        json.dump({
                            "processed_ids": list(processed_ids),
                            "total_processed": processed_count,
                            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }, f, indent=2)
                    logger.info(f"💾 Progress saved: {processed_count} workshops processed")
            else:
                failed_count += 1
                logger.error(f"❌ Failed to commit workshop {workshop_id}")
                
        except Exception as e:
            failed_count += 1
            logger.error(f"❌ Error processing workshop {workshop_id}: {e}")
            continue

    # Save final progress
    with open(progress_file, "w") as f:
        json.dump({
            "processed_ids": list(processed_ids),
            "total_processed": processed_count,
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }, f, indent=2)

    logger.info(f"🎉 Processing complete! Successfully processed: {processed_count}, Failed: {failed_count}")
    mongo_manager.close()
    return processed_count > 0

def test_ai_enhancement():
    """Test AI enhancement capabilities with a sample workshop"""
    print("🧪 Testing LLM enhancement...")
    
    # Sample workshop data
    sample_workshop = {
        'workshop_id': 'test_648',
        'title': 'Get Started with Oracle Cloud Infrastructure Core Services',
        'description': 'Explore basic OCI services: Networking, Compute, Storage and more.',
        'text_content': 'This workshop introduces you to Oracle Cloud Infrastructure (OCI) core services. You will learn about networking, compute, and storage services.',
        'url': '/pls/apex/r/dbpm/livelabs/view-workshop?wid=648'
    }
    
    enhancer = WorkshopEnhancer()
    if enhancer.client:
        enhanced = enhancer.enhance_workshop(sample_workshop)
        print("✅ LLM Enhancement Test Result:")
        print(f"Original: {sample_workshop['title']}")
        print(f"Enhanced Keywords: {enhanced.get('keywords', [])}")
        print(f"Enhanced Difficulty: {enhanced.get('difficulty', 'Unknown')}")
        print(f"Enhanced Category: {enhanced.get('category', 'Unknown')}")
        return True
    else:
        print("❌ LLM Enhancement Test Failed - OCI client not initialized")
        return False

def main():
    """Main function to run workshop AI enhancement pipeline"""
    # Test AI enhancement first
    print("🧪 Testing AI enhancement...")
    ai_test_success = test_ai_enhancement()
    
    if not ai_test_success:
        print("⚠️  AI enhancement test failed. Proceeding with basic import only.")
        success1 = import_raw_workshop_texts()
        if success1:
            print("✅ Successfully imported original workshop texts to MongoDB")
        else:
            print("❌ Failed to import workshop texts to MongoDB")
        return
    
    # Import original workshop texts
    print("\n📥 Importing raw workshop texts...")
    success1 = import_raw_workshop_texts()
    
    # Import AI-enhanced workshop texts
    print("\n🤖 Importing AI-enhanced workshop data...")
    success2 = import_ai_enhanced_workshops()
    
    if success1 and success2:
        print("✅ Workshop AI enhancement pipeline completed successfully")
    elif success1:
        print("✅ Raw workshop import succeeded, but AI enhancement failed")
    elif success2:
        print("✅ AI-enhanced workshop import succeeded, but raw import failed")
    else:
        print("❌ Workshop AI enhancement pipeline failed")

if __name__ == "__main__":
    main() 