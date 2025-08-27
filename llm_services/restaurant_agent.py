# restaurant_agent.py
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from typing import Dict, List, Any
import json
from datetime import datetime, timedelta

class RestaurantAIAgent:
    def __init__(self, restaurant_config: Dict[str, Any]):
        self.restaurant_config = restaurant_config
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,
            max_output_tokens=500
        )
        self.memory = ConversationBufferWindowMemory(
            k=10,
            return_messages=True,
            memory_key="chat_history"
        )
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create restaurant-specific tools"""
        return [
            Tool(
                name="check_availability",
                func=self.check_availability,
                description="Check table availability for a given date, time, and party size"
            ),
            Tool(
                name="get_menu_info",
                func=self.get_menu_info,
                description="Get information about menu items, prices, and ingredients"
            ),
            Tool(
                name="make_reservation",
                func=self.make_reservation,
                description="Create a reservation for the customer"
            ),
            Tool(
                name="check_hours",
                func=self.check_hours,
                description="Get restaurant operating hours for a specific day"
            ),
            Tool(
                name="process_order",
                func=self.process_order,
                description="Process a takeout or delivery order"
            ),
            Tool(
                name="get_wait_time",
                func=self.get_wait_time,
                description="Get current wait time for walk-ins"
            )
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """Create the main agent executor"""
        system_prompt = f"""You are an AI assistant for {self.restaurant_config['name']}.
        
        Restaurant Details:
        - Cuisine: {self.restaurant_config['cuisine']}
        - Hours: {self.restaurant_config['hours']}
        - Address: {self.restaurant_config['address']}
        - Phone: {self.restaurant_config['phone']}
        
        Your responsibilities:
        1. Handle reservations professionally and efficiently
        2. Answer questions about menu, hours, and location
        3. Process takeout orders accurately
        4. Provide wait time estimates
        5. Be friendly, helpful, and represent the restaurant well
        
        Special Instructions:
        - Always confirm reservation details before booking
        - Mention any daily specials when relevant
        - For large parties (8+), note that a deposit may be required
        - If fully booked, always offer alternative times
        """
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=5,
            early_stopping_method="generate"
        )
    
    def check_availability(self, date_time: str, party_size: int) -> str:
        """Check table availability"""
        # Integration with reservation system
        # This would connect to actual reservation database
        available_slots = []
        requested_time = datetime.fromisoformat(date_time)
        
        # Mock availability check
        for i in range(-1, 2):
            slot_time = requested_time + timedelta(hours=i*0.5)
            if self._is_slot_available(slot_time, party_size):
                available_slots.append(slot_time.strftime("%I:%M %p"))
        
        if available_slots:
            return f"Available times for party of {party_size}: {', '.join(available_slots)}"
        return f"No availability for party of {party_size} at requested time. Try different time?"
    
    def get_menu_info(self, query: str) -> str:
        """Retrieve menu information"""
        # This would connect to menu database
        menu_items = self.restaurant_config.get('menu_items', {})
        
        # Simple keyword matching - in production, use vector similarity
        relevant_items = []
        for item, details in menu_items.items():
            if query.lower() in item.lower() or query.lower() in details.get('description', '').lower():
                relevant_items.append(f"{item}: ${details['price']} - {details['description']}")
        
        if relevant_items:
            return "\n".join(relevant_items)
        return "I couldn't find specific menu items matching your query. Would you like to see our full menu?"
    
    def make_reservation(self, customer_info: Dict) -> str:
        """Create a reservation"""
        # Validate and create reservation
        reservation_id = f"RES-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Store in database (mock)
        reservation = {
            'id': reservation_id,
            'customer_name': customer_info['name'],
            'phone': customer_info['phone'],
            'date_time': customer_info['date_time'],
            'party_size': customer_info['party_size'],
            'special_requests': customer_info.get('special_requests', '')
        }
        
        return f"Reservation confirmed! ID: {reservation_id} for {customer_info['name']}, party of {customer_info['party_size']} on {customer_info['date_time']}"
    
    def process_order(self, order_details: Dict) -> str:
        """Process a takeout/delivery order"""
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Calculate total and estimated time
        total = sum(item['price'] * item['quantity'] for item in order_details['items'])
        prep_time = self._calculate_prep_time(order_details['items'])
        
        order = {
            'id': order_id,
            'items': order_details['items'],
            'total': total,
            'estimated_time': prep_time,
            'customer': order_details['customer']
        }
        
        return f"Order {order_id} confirmed! Total: ${total:.2f}. Ready in approximately {prep_time} minutes."
    
    def _is_slot_available(self, slot_time: datetime, party_size: int) -> bool:
        """Check if a specific time slot is available"""
        # Mock implementation - would check actual database
        import random
        return random.random() > 0.3
    
    def _calculate_prep_time(self, items: List[Dict]) -> int:
        """Calculate order preparation time"""
        # Simple calculation - would be more complex in production
        base_time = 15
        item_time = len(items) * 3
        return base_time + item_time