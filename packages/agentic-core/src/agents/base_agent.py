from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.render import format_tool_to_openai_function
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.messages import AIMessage, HumanMessage
from langchain.chat_models import ChatOpenAI
import logging

logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(
        self,
        tools: List[Any],
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.0,
        verbose: bool = False
    ):
        self.tools = tools
        self.model = ChatOpenAI(
            model_name=model_name,
            temperature=temperature
        )
        self.verbose = verbose
        
        # Convert tools to OpenAI function format
        self.functions = [format_tool_to_openai_function(t) for t in self.tools]
        
        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant for financial services observability."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create the agent
        self.agent = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: x["chat_history"],
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                ),
            }
            | self.prompt
            | self.model.bind(functions=self.functions)
            | OpenAIFunctionsAgentOutputParser()
        )
        
        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=verbose,
            handle_parsing_errors=True
        )
        
        self.chat_history: List[Dict[str, str]] = []

    async def run(
        self,
        input_text: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Run the agent with the given input and chat history.
        
        Args:
            input_text: The input text to process
            chat_history: Optional chat history to provide context
            
        Returns:
            Dict containing the agent's response and any additional information
        """
        try:
            if chat_history is None:
                chat_history = self.chat_history
                
            # Convert chat history to LangChain message format
            messages = []
            for msg in chat_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
            
            # Run the agent
            result = await self.agent_executor.ainvoke({
                "input": input_text,
                "chat_history": messages
            })
            
            # Update chat history
            self.chat_history.append({"role": "user", "content": input_text})
            self.chat_history.append({"role": "assistant", "content": result["output"]})
            
            return {
                "response": result["output"],
                "intermediate_steps": result.get("intermediate_steps", []),
                "chat_history": self.chat_history
            }
            
        except Exception as e:
            logger.error(f"Error running agent: {str(e)}")
            raise 