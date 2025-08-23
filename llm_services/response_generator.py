# response_generator.py
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import BaseOutputParser
from typing import Dict, Any, Optional
import json

class RestaurantResponseGenerator:
    def __init__(self, restaurant_config: Dict[str, Any]):
        self.restaurant_config = restaurant_config
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7
        )
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, ChatPromptTemplate]:
        """Load response templates for different scenarios"""
        return {
            "reservation_confirm": ChatPromptTemplate.from_messages([
                ("system", "You are confirming a reservation. Be professional and include all details."),
                ("human", "Confirm reservation for {name}, party of {size} on {date} at {time}")
            ]),
            
            "reservation_unavailable": ChatPromptTemplate.from_messages([
                ("system", "The requested time is not available. Offer alternatives politely."),
                ("human", "No availability for {size} people at {time}. Alternatives: {alternatives}")
            ]),
            
            "menu_response": ChatPromptTemplate.from_messages([
                ("system", "Provide menu information enthusiastically. Mention prices and any specials."),
                ("human", "Customer asking about: {query}. Menu items: {items}")
            ]),
            
            "order_confirmation": ChatPromptTemplate.from_messages([
                ("system", "Confirm the order clearly with all details and total price."),
                ("human", "Order details: {order_details}")
            ]),
            
            "review_response_positive": ChatPromptTemplate.from_messages([
                ("system", f"Respond to a positive review for {self.restaurant_config['name']}. Be grateful and personal."),
                ("human", "Review: {review_text}, Rating: {rating}/5")
            ]),
            
            "review_response_negative": ChatPromptTemplate.from_messages([
                ("system", f"Respond to a negative review for {self.restaurant_config['name']}. Be apologetic, professional, and offer to make things right."),
                ("human", "Review: {review_text}, Rating: {rating}/5, Issues mentioned: {issues}")
            ])
        }
    
    def generate_response(
        self, 
        intent: str, 
        context: Dict[str, Any],
        tone: str = "professional"
    ) -> str:
        """Generate contextual response based on intent"""
        
        # Select appropriate template
        template = self.templates.get(intent)
        if not template:
            return self._generate_generic_response(context)
        
        # Add tone modifier
        if tone == "casual":
            context["tone_instruction"] = "Be friendly and casual"
        elif tone == "formal":
            context["tone_instruction"] = "Be formal and professional"
        
        # Generate response
        response = self.llm.invoke(template.format_messages(**context))
        return response.content
    
    def _generate_generic_response(self, context: Dict) -> str:
        """Generate response for uncategorized intents"""
        generic_prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are an AI assistant for {self.restaurant_config['name']}. Help the customer with their inquiry."),
            ("human", "{query}")
        ])
        
        response = self.llm.invoke(
            generic_prompt.format_messages(query=context.get('query', ''))
        )
        return response.content
    
    def personalize_response(
        self, 
        base_response: str, 
        customer_data: Optional[Dict] = None
    ) -> str:
        """Add personalization to responses"""
        if not customer_data:
            return base_response
        
        personalization_prompt = ChatPromptTemplate.from_messages([
            ("system", "Personalize this restaurant response based on customer history."),
            ("human", """
            Base response: {base_response}
            Customer name: {name}
            Visit history: {visits}
            Preferences: {preferences}
            
            Add personal touches without changing the core message.
            """)
        ])
        
        response = self.llm.invoke(
            personalization_prompt.format_messages(
                base_response=base_response,
                name=customer_data.get('name', 'Guest'),
                visits=customer_data.get('visit_count', 0),
                preferences=customer_data.get('preferences', 'none noted')
            )
        )
        
        return response.content