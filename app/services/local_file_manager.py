import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import shutil
import json

from ..config.settings import settings

# Configurar logging
logger = logging.getLogger(__name__)

class LocalFileManager:
    """Gerenciador para salvar arquivos localmente como fallback do Google Drive"""
    
    def __init__(self, base_path: str = "nfes_storage"):
        """
        Inicializa o gerenciador de arquivos locais
        
        Args:
            base_path: Caminho base para armazenar os arquivos
        """
        self.base_path = Path(base_path)
        self._ensure_base_directory()
        logger.info(f"Local File Manager inicializado: {self.base_path.absolute()}")
    
    def _ensure_base_directory(self):
        """Garante que o diretório base existe"""
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Criar arquivo README para explicar a estrutura
        readme_path = self.base_path / "README.md"
        if not readme_path.exists():
            readme_content = """# Armazenamento Local de Notas Fiscais

Esta pasta contém os arquivos de notas fiscais organizados da seguinte forma:

```
nfes_storage/
├── CNPJ-12345678000199/
│   ├── 2025-06-28/
│   │   ├── nota1.pdf
│   │   ├── nota2.png
│   │   └── metadata.json
│   └── 2025-06-29/
│       └── ...
└── CNPJ-98765432000100/
    └── ...
```

- Cada CNPJ tem sua própria pasta
- Dentro de cada CNPJ, os arquivos são organizados por data
- Um arquivo `metadata.json` contém informações sobre os arquivos processados
"""
            readme_path.write_text(readme_content, encoding='utf-8')
    
    def _create_cnpj_folder_structure(self, cnpj: str) -> Dict[str, Path]:
        """Cria a estrutura de pastas para um CNPJ específico"""
        try:
            # Pasta do CNPJ
            cnpj_folder = self.base_path / f"CNPJ-{cnpj}"
            cnpj_folder.mkdir(parents=True, exist_ok=True)
            
            # Pasta da data atual
            current_date = datetime.now().strftime("%Y-%m-%d")
            date_folder = cnpj_folder / current_date
            date_folder.mkdir(parents=True, exist_ok=True)
            
            return {
                'cnpj_folder': cnpj_folder,
                'date_folder': date_folder,
                'cnpj_folder_name': f"CNPJ-{cnpj}",
                'date_folder_name': current_date
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar estrutura de pastas para CNPJ {cnpj}: {e}")
            raise
    
    def _update_metadata(self, date_folder: Path, file_info: Dict[str, Any]):
        """Atualiza o arquivo de metadados da pasta"""
        metadata_file = date_folder / "metadata.json"
        
        try:
            # Carregar metadados existentes
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {
                    'created_at': datetime.now().isoformat(),
                    'files': []
                }
            
            # Adicionar novo arquivo
            metadata['files'].append({
                'filename': file_info['filename'],
                'size': file_info['size'],
                'mime_type': file_info['mime_type'],
                'saved_at': datetime.now().isoformat(),
                'ocr_success': file_info.get('ocr_success', False)
            })
            
            metadata['updated_at'] = datetime.now().isoformat()
            
            # Salvar metadados
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao atualizar metadados: {e}")
    
    async def save_nota_fiscal_file(
        self,
        file_content: bytes,
        filename: str,
        cnpj: str,
        mime_type: str = None,
        ocr_success: bool = False
    ) -> Dict[str, Any]:
        """
        Salva um arquivo de nota fiscal localmente
        
        Args:
            file_content: Conteúdo do arquivo em bytes
            filename: Nome do arquivo
            cnpj: CNPJ do emissor
            mime_type: Tipo MIME do arquivo
            ocr_success: Se o OCR foi bem-sucedido
            
        Returns:
            Resultado do salvamento
        """
        try:
            # Criar estrutura de pastas
            folder_structure = self._create_cnpj_folder_structure(cnpj)
            
            # Caminho completo do arquivo
            file_path = folder_structure['date_folder'] / filename
            
            # Evitar sobrescrever arquivos
            counter = 1
            original_path = file_path
            while file_path.exists():
                name_parts = original_path.stem, counter, original_path.suffix
                file_path = original_path.parent / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                counter += 1
                filename = file_path.name
            
            # Salvar arquivo
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Atualizar metadados
            file_info = {
                'filename': filename,
                'size': len(file_content),
                'mime_type': mime_type or 'application/octet-stream',
                'ocr_success': ocr_success
            }
            
            self._update_metadata(folder_structure['date_folder'], file_info)
            
            logger.info(f"Arquivo '{filename}' salvo localmente: {file_path}")
            
            return {
                'success': True,
                'file_path': str(file_path),
                'filename': filename,
                'size': len(file_content),
                'folder_structure': {
                    'cnpj_folder': str(folder_structure['cnpj_folder']),
                    'date_folder': str(folder_structure['date_folder']),
                    'cnpj_folder_name': folder_structure['cnpj_folder_name'],
                    'date_folder_name': folder_structure['date_folder_name']
                },
                'full_path': f"{folder_structure['cnpj_folder_name']}/{folder_structure['date_folder_name']}/{filename}"
            }
            
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo localmente: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def list_files_by_cnpj(self, cnpj: str, date: str = None) -> Dict[str, Any]:
        """
        Lista arquivos de um CNPJ específico
        
        Args:
            cnpj: CNPJ do emissor
            date: Data específica (formato YYYY-MM-DD), se None lista todas as datas
            
        Returns:
            Lista de arquivos encontrados
        """
        try:
            cnpj_folder = self.base_path / f"CNPJ-{cnpj}"
            
            if not cnpj_folder.exists():
                return {
                    'success': True,
                    'files': [],
                    'message': f'Nenhuma pasta encontrada para CNPJ {cnpj}'
                }
            
            all_files = []
            
            if date:
                # Data específica
                date_folder = cnpj_folder / date
                if date_folder.exists():
                    files = self._list_files_in_folder(date_folder, date)
                    all_files.extend(files)
            else:
                # Todas as datas
                for date_folder in cnpj_folder.iterdir():
                    if date_folder.is_dir():
                        files = self._list_files_in_folder(date_folder, date_folder.name)
                        all_files.extend(files)
            
            return {
                'success': True,
                'files': all_files,
                'total_files': len(all_files),
                'cnpj': cnpj
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar arquivos do CNPJ {cnpj}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _list_files_in_folder(self, date_folder: Path, date_name: str) -> List[Dict[str, Any]]:
        """Lista arquivos em uma pasta de data específica"""
        files = []
        
        try:
            for file_path in date_folder.iterdir():
                if file_path.is_file() and file_path.name != 'metadata.json':
                    file_stat = file_path.stat()
                    files.append({
                        'filename': file_path.name,
                        'size': file_stat.st_size,
                        'date_folder': date_name,
                        'file_path': str(file_path),
                        'created_time': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                        'modified_time': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    })
        except Exception as e:
            logger.error(f"Erro ao listar arquivos na pasta {date_folder}: {e}")
        
        return files
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica o status do armazenamento local"""
        try:
            # Verificar se o diretório base existe e é acessível
            if not self.base_path.exists():
                return {
                    'status': 'unhealthy',
                    'error': f'Diretório base não existe: {self.base_path}'
                }
            
            # Verificar permissões de escrita
            test_file = self.base_path / '.health_check'
            try:
                test_file.write_text('test')
                test_file.unlink()
            except Exception as e:
                return {
                    'status': 'unhealthy',
                    'error': f'Sem permissão de escrita: {e}'
                }
            
            # Contar pastas e arquivos
            total_cnpj_folders = len([f for f in self.base_path.iterdir() if f.is_dir() and f.name.startswith('CNPJ-')])
            
            return {
                'status': 'healthy',
                'base_path': str(self.base_path.absolute()),
                'total_cnpj_folders': total_cnpj_folders,
                'writable': True
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

# Instância global do gerenciador local
local_file_manager = LocalFileManager()
