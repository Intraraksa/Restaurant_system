# intent_classifier.py
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Literal,Dict,Any
import json

class IntentClassification(BaseModel):
    primary_intent: Literal[
        "reservation", "menu_inquiry", "hours_inquiry", 
        "order_placement", "order_status", "complaint",
        "general_inquiry", "feedback"
    ] = Field(description="The main intent of the message")
    
    entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted entities from the message"
    )
    
    confidence: float = Field(
        description="Confidence score between 0 and 1"
    )
    
    requires_human: bool = Field(
        default=False,
        description="Whether this requires human intervention"
    )

class RestaurantIntentClassifier:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=IntentClassification)
        self.prompt = PromptTemplate(
            template="""Classify the following restaurant customer message.
            
            Message: {message}
            Context: {context}
            
            {format_instructions}
            
            Consider:
            1. What is the customer trying to accomplish?
            2. What specific information do they need?
            3. Is this urgent or time-sensitive?
            4. Does this require human intervention?
            
            Extract relevant entities such as:
            - Date and time for reservations
            - Party size
            - Menu items mentioned
            - Contact information
            - Special requests
            """,
            input_variables=["message", "context"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
    
    def classify(self, message: str, context: Dict = None) -> IntentClassification:
        """Classify a customer message"""
        context = context or {}
        
        formatted_prompt = self.prompt.format(
            message=message,
            context=json.dumps(context)
        )
        
        response = self.llm.predict(formatted_prompt)
        return self.parser.parse(response)
    
    def batch_classify(self, messages: List[str]) -> List[IntentClassification]:
        """Classify multiple messages efficiently"""
        classifications = []
        for message in messages:
            classifications.append(self.classify(message))
        return classifications