"""RAG 服务 - 代码索引和语义检索"""
import os
from typing import Optional
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from ..config import get_settings


class RAGService:
    """RAG 服务（基于 LangChain + ChromaDB）"""

    def __init__(self, persist_dir: str = "./data/chroma"):
        self.persist_dir = persist_dir
        self._embeddings = None
        self._text_splitter = None

    @property
    def embeddings(self):
        """懒加载 Embedding 模型"""
        if self._embeddings is None:
            settings = get_settings()
            self._embeddings = OpenAIEmbeddings(
                openai_api_key=settings.openai_api_key,
                openai_api_base=settings.openai_base_url
            )
        return self._embeddings

    @property
    def text_splitter(self):
        """懒加载文本分割器"""
        if self._text_splitter is None:
            self._text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\nclass ", "\ndef ", "\n\n", "\n", " "]
            )
        return self._text_splitter

    def _get_collection_name(self, owner: str, repo: str) -> str:
        """获取集合名称"""
        return f"project_{owner}_{repo}".replace("-", "_").replace(".", "_")

    async def index_code(self, owner: str, repo: str, files: list[tuple[str, str]]) -> bool:
        """索引代码文件

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            files: 文件列表，每个元素为 (file_path, content) 元组

        Returns:
            是否成功
        """
        try:
            collection_name = self._get_collection_name(owner, repo)

            # 创建 Document 对象
            documents = []
            for file_path, content in files:
                # 跳过空文件
                if not content or len(content.strip()) == 0:
                    continue

                doc = Document(
                    page_content=content,
                    metadata={
                        "file_path": file_path,
                        "owner": owner,
                        "repo": repo
                    }
                )
                # 按函数/类分块
                chunks = self.text_splitter.split_documents([doc])
                documents.extend(chunks)

            if not documents:
                print(f"[RAG] 没有可索引的文件: {owner}/{repo}")
                return False

            # 存储到 ChromaDB
            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_dir,
                collection_name=collection_name
            )

            print(f"[RAG] 索引完成: {owner}/{repo}, {len(documents)} 个文档块")
            return True

        except Exception as e:
            print(f"[RAG] 索引失败: {owner}/{repo}, {type(e).__name__}: {str(e)}")
            return False

    async def search(self, query: str, owner: str, repo: str, k: int = 5) -> list[dict]:
        """语义搜索

        Args:
            query: 查询文本
            owner: 仓库所有者
            repo: 仓库名称
            k: 返回结果数量

        Returns:
            搜索结果列表，每个元素包含 file_path 和 content
        """
        try:
            collection_name = self._get_collection_name(owner, repo)

            # 检查集合是否存在
            if not self._collection_exists(collection_name):
                print(f"[RAG] 集合不存在: {collection_name}")
                return []

            vectorstore = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings,
                collection_name=collection_name
            )

            results = vectorstore.similarity_search(
                query=query,
                k=k
            )

            # 格式化结果
            formatted_results = []
            for doc in results:
                formatted_results.append({
                    "file_path": doc.metadata.get("file_path", ""),
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })

            return formatted_results

        except Exception as e:
            print(f"[RAG] 搜索失败: {owner}/{repo}, {type(e).__name__}: {str(e)}")
            return []

    def _collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        try:
            # 尝试创建客户端并获取集合
            import chromadb
            client = chromadb.PersistentClient(path=self.persist_dir)
            collections = client.list_collections()
            return any(c.name == collection_name for c in collections)
        except Exception:
            return False

    def delete_collection(self, owner: str, repo: str) -> bool:
        """删除集合

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            是否成功
        """
        try:
            collection_name = self._get_collection_name(owner, repo)

            import chromadb
            client = chromadb.PersistentClient(path=self.persist_dir)

            if self._collection_exists(collection_name):
                client.delete_collection(collection_name)
                print(f"[RAG] 删除集合: {collection_name}")

            return True

        except Exception as e:
            print(f"[RAG] 删除集合失败: {owner}/{repo}, {type(e).__name__}: {str(e)}")
            return False


# 全局实例
rag_service = RAGService()
