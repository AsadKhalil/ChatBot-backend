from abc import abstractmethod
import logging
import os
import traceback
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from langchain.agents import tool, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from app.src import constants
from sqlalchemy import create_engine
from app.src.modules.databases import PGVectorManager, get_alchemy_conn_string, ConversationDB
from app.src.config import USE_OPENAI, get_model_name
from app.src.prompts import (
    get_prompt_template,
    get_project_extra_info,
    get_model_config,
    get_prompt_params,
)

INPUT_KEY = "{input}"


class Agent:
    @abstractmethod
    async def _create_agent(self) -> None:
        pass

    @abstractmethod
    async def _build_prompt(self) -> None:
        pass

    @abstractmethod
    async def qa(self, query: str, history: list) -> str:
        pass


class LLMAgentFactory:
    """class for llm agent"""

    async def create(self) -> Agent:
        logger = logging.getLogger("LLMAgentFactory")

        # REDIS_URL = os.environ.get("REDIS_URL")
        # PROJECT_NAME = os.environ.get("PROJECT_NAME")
        # redis = aioredis.from_url(
        #     REDIS_URL, encoding="utf-8", decode_responses=True)
        # llm_id = await redis.get(f"{PROJECT_NAME}:llm_model",)
        # logger.info("llm_id: %s", llm_id)

        if USE_OPENAI:
            agent = OPENAIAgent()
            return agent
        else:
            agent = OllamaAgent()
            return agent


class OPENAIAgent(Agent):
    """class for function calling rag agent"""

    def __init__(self) -> None:
        self.logger = logging.getLogger("OPENAIAgent")
        self.conn_string = get_alchemy_conn_string()
        self.logger.info("connection string: %s", self.conn_string)
        self.engine = create_engine(self.conn_string)
        self.db = ConversationDB()

    async def _create_agent(self) -> None:
        self.llm = ChatOpenAI(model=self.llm_model_id, temperature=0)

        @tool
        async def semantic_search(search_term: str):
            """
            This function utilizes a vector store to retrieve relevant documents based on the semantic similarity of their content to the provided search term.
            """
            result = await self.db.get_active_files()
            VECTORSTORE_COLLECTION_NAME = os.environ.get(
                "VECTORSTORE_COLLECTION_NAME")
            pgmanager = PGVectorManager()
            retriever = pgmanager.return_vector_store(
                VECTORSTORE_COLLECTION_NAME, async_mode=False)
            context = ''
            active_files = []
            for filename_tuple in result:
                filename = filename_tuple[0]
                active_files.append(filename)

            docs = retriever.similarity_search(
                search_term, k=5, filter={"source": active_files}
            )
            for doc in docs:
                content = doc.page_content
                context = context + content
            pgmanager.close()
            return context

        tools = [semantic_search]

        self.llm_with_tools = self.llm.bind_tools(tools)

        MEMORY_KEY = "chat_history"

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.prompt,
                ),
                MessagesPlaceholder(variable_name=MEMORY_KEY),
                ("user", INPUT_KEY),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_to_openai_tool_messages(
                    x["intermediate_steps"]
                ),
                "chat_history": lambda x: x["chat_history"],
            }
            | prompt
            | self.llm_with_tools
            | OpenAIToolsAgentOutputParser()
        )
        self.agent_executor = AgentExecutor(
            agent=agent, tools=tools, verbose=True, return_intermediate_steps=True,)

    async def _build_prompt(self):
        PROJECT_NAME = os.environ.get("PROJECT_NAME")
        EXTRA_INFO = get_project_extra_info(PROJECT_NAME)

        # Get prompt parameters from environment variables
        self.llm_model_id = get_model_name(os.environ.get("LLM_MODEL", get_model_config(USE_OPENAI)))
        params = get_prompt_params()

        self.prompt = get_prompt_template(
            persona=params["persona"],
            glossary=params["glossary"],
            tone=params["tone"],
            response_length=params["response_length"],
            content=params["content"],
            extra_info=EXTRA_INFO
        )

    async def qa(self, query, chat_history):
        try:
            extracted_data = []

            for item in chat_history:
                human = {"role": "human", "content": item["prompt"]}
                extracted_data.append(human)
                if item["response"] != None:
                    assistant = {"role": "assistant",
                                 "content": item["response"]}
                    extracted_data.append(assistant)

            response = await self.agent_executor.ainvoke(
                {"input": query, "chat_history": extracted_data})

            self.engine.dispose()

            result = response["output"]
            self.logger.critical("result: " + result)
            if response["intermediate_steps"]:
                context = ''
                for step in response['intermediate_steps']:
                    if isinstance(step[-1], str):
                        context = context + ';' + step[-1]
                    else:
                        context = context + ';' + step[-1][1]

                return result, context

            return result, ""
        except Exception:
            self.logger.exception(traceback.format_exc())


class OllamaAgent(Agent):
    """class for Ollama-based rag agent"""

    def __init__(self) -> None:
        self.logger = logging.getLogger("OllamaAgent")
        self.conn_string = get_alchemy_conn_string()
        self.logger.info("connection string: %s", self.conn_string)
        self.engine = create_engine(self.conn_string)
        self.db = ConversationDB()

    async def _create_agent(self) -> None:
        self.llm = ChatOllama(model=self.llm_model_id, temperature=0)
        
        # Initialize vector store
        self.VECTORSTORE_COLLECTION_NAME = os.environ.get("VECTORSTORE_COLLECTION_NAME")
        self.pgmanager = PGVectorManager()
        self.retriever = self.pgmanager.return_vector_store(
            self.VECTORSTORE_COLLECTION_NAME, async_mode=False
        )

    async def _build_prompt(self):
        PROJECT_NAME = os.environ.get("PROJECT_NAME")
        EXTRA_INFO = get_project_extra_info(PROJECT_NAME)

        # Get prompt parameters from environment variables
        self.llm_model_id = get_model_name(os.environ.get("LLM_MODEL", get_model_config(False)))
        params = get_prompt_params()

        self.prompt = get_prompt_template(
            persona=params["persona"],
            glossary=params["glossary"],
            tone=params["tone"],
            response_length=params["response_length"],
            content=params["content"],
            extra_info=EXTRA_INFO
        )

    async def qa(self, query, chat_history):
        try:
            # Get active files
            result = await self.db.get_active_files()
            active_files = [filename_tuple[0] for filename_tuple in result]

            # Perform semantic search without filter first
            docs = self.retriever.similarity_search(query, k=20)  # Get more results than needed
            
            # Filter results manually
            filtered_docs = []
            for doc in docs:
                if doc.metadata.get('source') in active_files:
                    filtered_docs.append(doc)
                if len(filtered_docs) >= 5:  # Stop once we have enough filtered results
                    break

            context = ""
            for doc in filtered_docs:
                context += doc.page_content + "\n"

            # Prepare chat history
            extracted_data = []
            for item in chat_history:
                human = {"role": "human", "content": item["prompt"]}
                extracted_data.append(human)
                if item["response"] is not None:
                    assistant = {"role": "assistant", "content": item["response"]}
                    extracted_data.append(assistant)

            # Create prompt with context
            full_prompt = f"{self.prompt}\n\nContext:\n{context}\n\nUser: {query}"
            
            # Get response from LLM
            response = await self.llm.ainvoke(full_prompt)
            result = response.content

            self.engine.dispose()
            self.pgmanager.close()

            return result, context
        except Exception:
            self.logger.exception(traceback.format_exc())
            return "I apologize, but I encountered an error while processing your request.", ""
