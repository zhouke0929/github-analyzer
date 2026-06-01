"""RAG 服务 - 代码索引和语义检索"""
import os
import ast
import requests
from typing import Optional, List
from langchain_chroma import Chroma
from langchain.embeddings.base import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from ..config import get_settings


class DashScopeEmbeddings(Embeddings):
    """阿里云 DashScope Embedding 模型"""

    def __init__(self, api_key: str, base_url: str, model: str = "text-embedding-v4"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量向量化文本（分批处理 + 重试）"""
        import time

        all_embeddings = []
        batch_size = 10  # DashScope 限制每批最多 10 个

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            # 截断超长文本
            batch = [t[:8000] if len(t) > 8000 else t for t in batch]

            # 重试逻辑（指数退避）
            for attempt in range(3):
                try:
                    url = f"{self.base_url}/embeddings"
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    data = {"model": self.model, "input": batch}
                    response = requests.post(url, headers=headers, json=data, timeout=60)
                    response.raise_for_status()
                    result = response.json()
                    all_embeddings.extend([item["embedding"] for item in result["data"]])
                    break
                except requests.exceptions.HTTPError as e:
                    if attempt < 2 and response.status_code in (429, 500, 502, 503):
                        time.sleep(2 ** attempt)
                        continue
                    raise

            # 批次间延迟
            if i + batch_size < len(texts):
                time.sleep(0.5)

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """向量化单个文本"""
        return self.embed_documents([text])[0]


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
            self._embeddings = DashScopeEmbeddings(
                api_key=settings.embedding_api_key,
                base_url=settings.embedding_base_url,
                model=settings.embedding_model
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

    def _ast_split_python(self, content: str, file_path: str) -> list:
        """使用 AST 分割 Python 代码，保留函数/类边界

        Args:
            content: Python 代码内容
            file_path: 文件路径

        Returns:
            Document 列表
        """
        documents = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # 语法错误时回退到字符分割
            doc = Document(page_content=content, metadata={"file_path": file_path})
            return self.text_splitter.split_documents([doc])

        lines = content.split('\n')

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start_line = node.lineno - 1  # ast 使用 1-based 行号
                end_line = getattr(node, 'end_lineno', None)

                if end_line is None:
                    # 估算结束行
                    end_line = min(start_line + 50, len(lines))

                chunk_content = '\n'.join(lines[start_line:end_line])

                # 超大块进一步分割
                if len(chunk_content) > 1500:
                    sub_doc = Document(page_content=chunk_content, metadata={"file_path": file_path})
                    sub_chunks = self.text_splitter.split_documents([sub_doc])
                    documents.extend(sub_chunks)
                else:
                    documents.append(Document(
                        page_content=chunk_content,
                        metadata={"file_path": file_path}
                    ))

        # 没有函数/类时回退到全文分割
        if not documents:
            doc = Document(page_content=content, metadata={"file_path": file_path})
            documents = self.text_splitter.split_documents([doc])

        return documents

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

                # Python 文件使用 AST 分割，其他文件使用字符分割
                if file_path.endswith('.py'):
                    chunks = self._ast_split_python(content, file_path)
                else:
                    doc = Document(
                        page_content=content,
                        metadata={"file_path": file_path}
                    )
                    chunks = self.text_splitter.split_documents([doc])

                # 添加公共元数据
                for chunk in chunks:
                    chunk.metadata.update({"owner": owner, "repo": repo})
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
