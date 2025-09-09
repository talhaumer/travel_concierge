import os
from langgraph.graph import StateGraph, END
from .state import TravelState
from .agents import (
    UserInputAgent,
    ResearchAgent,
    PlannerAgent,
    WriterAgent,
    ReviewerAgent,
)


GROQ_API_KEY =  os.getenv("GROQ_API_KEY")


class TravelGraph:
    def __init__(self):
        self.graph = StateGraph(TravelState)

        # Initialize agents
        self.user_input_agent = UserInputAgent(api_key=GROQ_API_KEY)
        self.research_agent = ResearchAgent(api_key=GROQ_API_KEY)
        self.planner_agent = PlannerAgent(api_key=GROQ_API_KEY)
        self.writer_agent = WriterAgent(api_key=GROQ_API_KEY)
        self.reviewer_agent = ReviewerAgent(api_key=GROQ_API_KEY)

        # Add nodes
        self.graph.add_node("get_user_input", self.user_input_agent.process)
        self.graph.add_node("research_destination", self.research_agent.process)
        self.graph.add_node("plan_itinerary", self.planner_agent.process)
        self.graph.add_node("review_itinerary", self.reviewer_agent.process)
        self.graph.add_node("generate_output", self.writer_agent.process)

        # Define the graph flow
        self.graph.set_entry_point("get_user_input")

        self.graph.add_edge("get_user_input", "research_destination")
        self.graph.add_edge("research_destination", "plan_itinerary")
        self.graph.add_conditional_edges(
            "plan_itinerary",
            self.should_review,
            {"review": "review_itinerary", "continue": "generate_output"},
        )
        self.graph.add_edge("review_itinerary", "generate_output")
        self.graph.add_edge("generate_output", END)

        # Compile the graph
        self.compiled_graph = self.graph.compile()

    def should_review(self, state: TravelState) -> str:
        """Determine if itinerary needs review"""
        if state.violations or state.needs_fallback or state.circuit_breaker_count > 0:
            return "review"
        return "continue"

    def invoke(self, user_input: str):
        """Execute the travel planning graph"""
        initial_state = TravelState(user_input=user_input)
        return self.compiled_graph.invoke(initial_state)

