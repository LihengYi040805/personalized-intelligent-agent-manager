"""
文档解析服务 - 支持PDF、Word等格式
"""
import os
import requests
from typing import Optional
import PyPDF2
from docx import Document


class DocumentParser:
    """文档解析类"""
    
    # Deepseek-OCR服务配置
    OCR_SERVICE_URL = os.getenv('DEEPSEEK_OCR_URL', 'http://localhost:8000/api/ocr/upload')
    USE_OCR = os.getenv('USE_DEEPSEEK_OCR', 'false').lower() == 'true'
    
    @staticmethod
    def parse_pdf_with_ocr(file_path: str) -> str:
        """
        使用Deepseek-OCR解析PDF文件（支持扫描版PDF）
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            str: OCR识别的Markdown格式文本
        """
        try:
            print(f"  🔍 使用Deepseek-OCR识别PDF...")
            
            with open(file_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(file_path), f, 'application/pdf')
                }
                
                # 发送OCR请求
                response = requests.post(
                    DocumentParser.OCR_SERVICE_URL,
                    files=files,
                    timeout=300  # 5分钟超时
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get('status') == 'success':
                        markdown_text = result.get('markdown', '')
                        
                        # 移除页面分隔符，保留内容
                        markdown_text = markdown_text.replace('<--- Page Split --->', '\n\n')
                        
                        print(f"  ✅ OCR识别成功，提取了 {len(markdown_text)} 个字符")
                        return markdown_text.strip()
                    else:
                        raise Exception(f"OCR识别失败: {result.get('message', '未知错误')}")
                else:
                    raise Exception(f"OCR服务请求失败: HTTP {response.status_code}")
                    
        except requests.exceptions.ConnectionError:
            raise Exception(f"无法连接到Deepseek-OCR服务 ({DocumentParser.OCR_SERVICE_URL})，请确保服务已启动")
        except requests.exceptions.Timeout:
            raise Exception("OCR识别超时，文档可能过大")
        except Exception as e:
            raise Exception(f"Deepseek-OCR解析失败: {str(e)}")
    
    @staticmethod
    def parse_pdf(file_path: str, use_ocr: bool = None) -> str:
        """
        解析PDF文件
        
        Args:
            file_path: PDF文件路径
            use_ocr: 是否使用OCR（None时根据配置决定）
            
        Returns:
            str: 提取的文本内容
        """
        # 确定是否使用OCR
        if use_ocr is None:
            use_ocr = DocumentParser.USE_OCR
        
        # 如果启用OCR，优先使用OCR
        if use_ocr:
            try:
                return DocumentParser.parse_pdf_with_ocr(file_path)
            except Exception as e:
                print(f"  ⚠️  OCR解析失败，回退到PyPDF2: {str(e)}")
                # OCR失败，回退到PyPDF2
        
        # 使用PyPDF2解析
        try:
            print(f"  📄 使用PyPDF2解析PDF...")
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            extracted_text = text.strip()
            
            # 如果PyPDF2提取的文本太少，可能是扫描版PDF，尝试OCR
            if len(extracted_text) < 100 and not use_ocr:
                print(f"  ⚠️  PyPDF2提取文本过少（{len(extracted_text)}字符），可能是扫描版PDF")
                print(f"  💡 提示：可以启用Deepseek-OCR来识别扫描版PDF")
            
            return extracted_text
        except Exception as e:
            raise Exception(f"PDF解析失败: {str(e)}")
    
    @staticmethod
    def parse_docx(file_path: str) -> str:
        """
        解析Word文件
        
        Args:
            file_path: Word文件路径
            
        Returns:
            str: 提取的文本内容
        """
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise Exception(f"Word文档解析失败: {str(e)}")
    
    @staticmethod
    def parse_txt(file_path: str) -> str:
        """
        解析文本文件
        
        Args:
            file_path: 文本文件路径
            
        Returns:
            str: 文本内容
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, 'r', encoding='gbk') as file:
                return file.read().strip()
        except Exception as e:
            raise Exception(f"文本文件解析失败: {str(e)}")
    
    @staticmethod
    def parse_markdown(file_path: str) -> str:
        """
        解析Markdown文件
        
        Args:
            file_path: Markdown文件路径
            
        Returns:
            str: 提取的文本内容
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                # Markdown文件可以直接读取，AI模型能够理解Markdown格式
                return content
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, 'r', encoding='gbk') as file:
                return file.read().strip()
        except Exception as e:
            raise Exception(f"Markdown文件解析失败: {str(e)}")
    
    @staticmethod
    def parse_document(file_path: str, use_ocr: bool = None) -> str:
        """
        根据文件类型自动选择解析方法
        
        Args:
            file_path: 文件路径
            use_ocr: 是否使用OCR（仅对PDF有效）
            
        Returns:
            str: 提取的文本内容
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext == '.pdf':
            return DocumentParser.parse_pdf(file_path, use_ocr=use_ocr)
        elif ext in ['.docx', '.doc']:
            return DocumentParser.parse_docx(file_path)
        elif ext in ['.md', '.markdown']:
            return DocumentParser.parse_markdown(file_path)
        elif ext == '.txt':
            return DocumentParser.parse_txt(file_path)
        else:
            raise Exception(f"不支持的文件格式: {ext}，支持的格式：.txt, .md, .markdown, .pdf, .doc, .docx")

