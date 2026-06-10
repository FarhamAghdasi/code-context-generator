# core/smart_splitter.py (updated with hybrid splitting)
"""Advanced smart splitting module with content-aware boundaries."""

import os
import re
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from colorama import Fore, Style


class SplitStrategy(Enum):
    """Splitting strategies for output content."""
    BY_FILES = "by_files"
    BY_SIZE = "by_size"
    BY_SECTIONS = "by_sections"
    BY_CHARACTERS = "by_characters"
    BALANCED = "balanced"
    HYBRID = "hybrid"  # NEW: Both file count AND size limit


class BoundaryType(Enum):
    """Content boundary types for clean splitting."""
    WORD = "word"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    FUNCTION = "function"
    CLASS = "class"
    FILE = "file"
    MARKDOWN_HEADING = "markdown_heading"
    CODE_BLOCK = "code_block"


class SmartSplitter:
    """Advanced content splitter with intelligent boundary detection."""
    
    def __init__(self):
        """Initialize SmartSplitter with boundary patterns."""
        self.boundary_patterns = {
            BoundaryType.WORD: r'\s+',
            BoundaryType.SENTENCE: r'[.!?]\s+(?=[A-Z])',
            BoundaryType.PARAGRAPH: r'\n\s*\n',
            BoundaryType.FUNCTION: r'\n(def|function|async def|private|public|protected)\s+\w+\s*\([^)]*\)\s*[:{]',
            BoundaryType.CLASS: r'\n(class|interface|trait)\s+\w+',
            BoundaryType.MARKDOWN_HEADING: r'\n#{1,6}\s+',
            BoundaryType.CODE_BLOCK: r'```[\s\S]*?```'
        }
        
        # Language-specific patterns
        self.lang_patterns = {
            'python': {
                'function': r'\n(@\w+\s+)?def\s+\w+\s*\([^)]*\)\s*:',
                'class': r'\nclass\s+\w+[:\(]',
                'import': r'\n(import|from)\s+\w+'
            },
            'javascript': {
                'function': r'\n(function\s+\w+\s*\([^)]*\)\s*\{|\w+\s*=\s*\([^)]*\)\s*=>\s*\{)',
                'class': r'\nclass\s+\w+\s*\{',
                'import': r'\nimport\s+.*?from'
            },
            'java': {
                'function': r'\n\s*(public|private|protected)\s+\w+\s+\w+\s*\([^)]*\)\s*\{',
                'class': r'\n\s*(public\s+)?class\s+\w+\s*\{',
                'import': r'\nimport\s+.*?;'
            },
            'go': {
                'function': r'\nfunc\s+\w+\s*\([^)]*\)\s*\{',
                'class': r'\ntype\s+\w+\s+struct\s*\{',
                'import': r'\nimport\s+\('
            }
        }
    
    def get_split_preferences_interactive(self) -> Dict[str, Any]:
        """Get splitting preferences interactively from user."""
        print(f"\n{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 15} ADVANCED SPLITTER CONFIGURATION {'=' * 15}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")
        
        # Step 1: Split strategy
        print(f"{Fore.YELLOW}📊 SPLIT STRATEGY:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Choose how you want to split the output:{Style.RESET_ALL}\n")
        
        strategies = [
            ("Split by file count (create exactly N files)", SplitStrategy.BY_FILES),
            ("Split by size (max MB per file)", SplitStrategy.BY_SIZE),
            ("Split by logical sections (functions/classes/headings)", SplitStrategy.BY_SECTIONS),
            ("Split by character count", SplitStrategy.BY_CHARACTERS),
            ("Balanced splitting (intelligent auto-balancing)", SplitStrategy.BALANCED),
            ("🔹 HYBRID MODE: Both file count AND size limit (BEST for AI) 🔹", SplitStrategy.HYBRID)
        ]
        
        for idx, (desc, _) in enumerate(strategies, 1):
            if "HYBRID" in desc:
                print(f"  {Fore.MAGENTA}{idx}.{Style.RESET_ALL} {Fore.CYAN}{desc}{Style.RESET_ALL}")
            else:
                print(f"  {Fore.GREEN}{idx}.{Style.RESET_ALL} {desc}")
        
        while True:
            try:
                print()
                choice = int(input(f"{Fore.YELLOW}👉 Enter your choice (1-{len(strategies)}): {Style.RESET_ALL}").strip())
                if 1 <= choice <= len(strategies):
                    strategy = strategies[choice - 1][1]
                    break
                print(f"{Fore.RED}❌ Invalid choice. Please try again.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}❌ Please enter a valid number.{Style.RESET_ALL}")
        
        # Step 2: Get limits based on strategy
        limit = None
        max_files = None
        max_size_mb = None
        
        if strategy == SplitStrategy.BY_FILES:
            print(f"\n{Fore.YELLOW}📁 FILE COUNT LIMIT:{Style.RESET_ALL}")
            while True:
                try:
                    limit = int(input(f"{Fore.YELLOW}👉 Maximum number of split files (1-100): {Style.RESET_ALL}").strip())
                    if 1 <= limit <= 100:
                        break
                    print(f"{Fore.RED}❌ Please enter a number between 1 and 100.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED}❌ Please enter a valid number.{Style.RESET_ALL}")
        
        elif strategy == SplitStrategy.BY_SIZE:
            print(f"\n{Fore.YELLOW}💾 SIZE LIMIT PER FILE:{Style.RESET_ALL}")
            while True:
                try:
                    mb = float(input(f"{Fore.YELLOW}👉 Maximum size per file (MB, 0.1-50): {Style.RESET_ALL}").strip())
                    if 0.1 <= mb <= 50:
                        limit = int(mb * 1024 * 1024)
                        print(f"{Fore.CYAN}   → That's approximately {limit:,} characters{Style.RESET_ALL}")
                        break
                    print(f"{Fore.RED}❌ Please enter a size between 0.1 and 50 MB.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED}❌ Please enter a valid number.{Style.RESET_ALL}")
        
        elif strategy == SplitStrategy.BY_CHARACTERS:
            print(f"\n{Fore.YELLOW}📝 CHARACTER LIMIT:{Style.RESET_ALL}")
            while True:
                try:
                    limit = int(input(f"{Fore.YELLOW}👉 Maximum characters per file (1000-500000): {Style.RESET_ALL}").strip())
                    if 1000 <= limit <= 500000:
                        break
                    print(f"{Fore.RED}❌ Please enter a number between 1000 and 500,000.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED}❌ Please enter a valid number.{Style.RESET_ALL}")
        
        elif strategy == SplitStrategy.HYBRID:
            print(f"\n{Fore.MAGENTA}🔹 HYBRID MODE CONFIGURATION 🔹{Style.RESET_ALL}")
            print(f"{Fore.CYAN}This mode will split files based on BOTH limits:{Style.RESET_ALL}")
            print(f"{Fore.CYAN}- Maximum number of files{Style.RESET_ALL}")
            print(f"{Fore.CYAN}- Maximum size per file{Style.RESET_ALL}")
            print(f"{Fore.CYAN}The splitter will try to satisfy both conditions.{Style.RESET_ALL}\n")
            
            # Get max files
            while True:
                try:
                    max_files = int(input(f"{Fore.YELLOW}👉 Maximum number of split files (1-100): {Style.RESET_ALL}").strip())
                    if 1 <= max_files <= 100:
                        break
                    print(f"{Fore.RED}❌ Please enter a number between 1 and 100.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED}❌ Please enter a valid number.{Style.RESET_ALL}")
            
            # Get max size per file
            while True:
                try:
                    max_size_mb = float(input(f"{Fore.YELLOW}👉 Maximum size per file (MB, 0.1-50): {Style.RESET_ALL}").strip())
                    if 0.1 <= max_size_mb <= 50:
                        limit = int(max_size_mb * 1024 * 1024)
                        print(f"{Fore.CYAN}   → That's approximately {limit:,} characters per file{Style.RESET_ALL}")
                        break
                    print(f"{Fore.RED}❌ Please enter a size between 0.1 and 50 MB.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED}❌ Please enter a valid number.{Style.RESET_ALL}")
        
        # Step 3: Boundary type for clean splitting
        print(f"\n{Fore.YELLOW}🎯 SPLIT BOUNDARY TYPE:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}How should content be split? (Choose for clean boundaries){Style.RESET_ALL}\n")
        
        boundary_options = [
            ("Split at word boundaries (never cut words mid-word)", BoundaryType.WORD),
            ("Split at sentence boundaries (end of sentences . ! ?)", BoundaryType.SENTENCE),
            ("Split at paragraph boundaries (between paragraphs)", BoundaryType.PARAGRAPH),
            ("Split at function boundaries (preserve whole functions)", BoundaryType.FUNCTION),
            ("Split at class boundaries (preserve whole classes)", BoundaryType.CLASS),
            ("Split at markdown headings (for docs/README files)", BoundaryType.MARKDOWN_HEADING),
        ]
        
        for idx, (desc, _) in enumerate(boundary_options, 1):
            print(f"  {Fore.GREEN}{idx}.{Style.RESET_ALL} {desc}")
        
        while True:
            try:
                print()
                choice = int(input(f"{Fore.YELLOW}👉 Enter your choice (1-{len(boundary_options)}): {Style.RESET_ALL}").strip())
                if 1 <= choice <= len(boundary_options):
                    boundary_type = boundary_options[choice - 1][1]
                    break
                print(f"{Fore.RED}❌ Invalid choice. Please try again.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}❌ Please enter a valid number.{Style.RESET_ALL}")
        
        # Step 4: Overlap for context preservation
        print(f"\n{Fore.YELLOW}🔄 CONTEXT OVERLAP:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Add context from previous file to help AI understand continuity{Style.RESET_ALL}\n")
        
        overlap_options = [
            ("No overlap (smallest files, no context)", 0),
            ("Small overlap (50-100 chars) - RECOMMENDED for code", 100),
            ("Medium overlap (200-300 chars) - Good for documents", 250),
            ("Large overlap (500 chars) - Best for large files", 500)
        ]
        
        for idx, (desc, _) in enumerate(overlap_options, 1):
            print(f"  {Fore.GREEN}{idx}.{Style.RESET_ALL} {desc}")
        
        while True:
            try:
                print()
                choice = int(input(f"{Fore.YELLOW}👉 Enter your choice (1-{len(overlap_options)}): {Style.RESET_ALL}").strip())
                if 1 <= choice <= len(overlap_options):
                    overlap_chars = overlap_options[choice - 1][1]
                    if overlap_chars > 0:
                        print(f"{Fore.CYAN}   → Will add {overlap_chars} characters of context from previous file{Style.RESET_ALL}")
                    break
                print(f"{Fore.RED}❌ Invalid choice.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}❌ Please enter a valid number.{Style.RESET_ALL}")
        
        # Step 5: Show summary
        print(f"\n{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ SPLIT CONFIGURATION SUMMARY:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        
        if strategy == SplitStrategy.HYBRID:
            print(f"  Strategy:      {Fore.MAGENTA}{strategy.value.upper()} (BEST for AI){Style.RESET_ALL}")
            print(f"  Max Files:     {Fore.YELLOW}{max_files}{Style.RESET_ALL}")
            print(f"  Max Size:      {Fore.YELLOW}{max_size_mb} MB ({limit:,} chars){Style.RESET_ALL}")
        else:
            print(f"  Strategy:      {Fore.YELLOW}{strategy.value}{Style.RESET_ALL}")
            if limit:
                if strategy == SplitStrategy.BY_SIZE:
                    print(f"  Limit:         {Fore.YELLOW}{limit // (1024*1024)} MB ({limit:,} bytes){Style.RESET_ALL}")
                else:
                    print(f"  Limit:         {Fore.YELLOW}{limit:,}{Style.RESET_ALL}")
        
        print(f"  Boundary:      {Fore.YELLOW}{boundary_type.value}{Style.RESET_ALL}")
        print(f"  Overlap:       {Fore.YELLOW}{overlap_chars} chars{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")
        
        confirm = input(f"{Fore.YELLOW}Proceed with this configuration? (y/n): {Style.RESET_ALL}").strip().lower()
        if confirm != 'y':
            print(f"{Fore.CYAN}Restarting configuration...{Style.RESET_ALL}")
            return self.get_split_preferences_interactive()
        
        result = {
            'strategy': strategy,
            'limit': limit,
            'boundary_type': boundary_type,
            'overlap_chars': overlap_chars,
            'language': 'auto-detect',
            'preserve_code_blocks': True,
            'preserve_markdown': True
        }
        
        # Add hybrid-specific params
        if strategy == SplitStrategy.HYBRID:
            result['max_files'] = max_files
            result['max_size_mb'] = max_size_mb
        
        return result
    
    def split_content(self, content: str, preferences: Dict[str, Any]) -> List[str]:
        """Split content based on preferences."""
        strategy = preferences['strategy']
        limit = preferences.get('limit')
        boundary_type = preferences.get('boundary_type', BoundaryType.SENTENCE)
        overlap = preferences.get('overlap_chars', 100)
        
        print(f"\n{Fore.CYAN}🔪 Splitting content using {strategy.value} strategy...{Style.RESET_ALL}")
        
        if strategy == SplitStrategy.BY_FILES and limit:
            return self._split_by_file_count(content, limit, boundary_type, overlap)
        elif strategy == SplitStrategy.BY_SIZE and limit:
            return self._split_by_size(content, limit, boundary_type, overlap)
        elif strategy == SplitStrategy.BY_SECTIONS:
            return self._split_by_sections(content, boundary_type, overlap)
        elif strategy == SplitStrategy.BY_CHARACTERS and limit:
            return self._split_by_characters(content, limit, boundary_type, overlap)
        elif strategy == SplitStrategy.HYBRID:
            max_files = preferences.get('max_files', 10)
            max_size = preferences.get('limit', 10 * 1024 * 1024)
            return self._split_hybrid(content, max_files, max_size, boundary_type, overlap)
        else:  # BALANCED
            return self._split_balanced(content, boundary_type, overlap)
    
    def _split_hybrid(self, content: str, max_files: int, max_size: int, 
                      boundary_type: BoundaryType, overlap: int) -> List[str]:
        """
        Hybrid splitting: respects BOTH file count AND size limits.
        Creates as many files as needed up to max_files, 
        but ensures each file doesn't exceed max_size.
        """
        total_size = len(content)
        min_required_files = (total_size + max_size - 1) // max_size
        
        # Calculate optimal number of files
        optimal_files = min(max_files, max(min_required_files, 1))
        
        # Target size per file
        target_size = total_size // optimal_files
        target_size = min(target_size, max_size)
        
        print(f"{Fore.CYAN}   📊 Hybrid Analysis:{Style.RESET_ALL}")
        print(f"      Total size: {total_size:,} chars")
        print(f"      Max files allowed: {max_files}")
        print(f"      Max size per file: {max_size:,} chars")
        print(f"      Min files needed: {min_required_files}")
        print(f"      Optimal files: {optimal_files}")
        print(f"      Target per file: {target_size:,} chars")
        
        # Perform the split
        chunks = []
        current_pos = 0
        
        for file_num in range(optimal_files):
            is_last = (file_num == optimal_files - 1)
            
            if is_last:
                # Last chunk takes remaining content
                chunk = content[current_pos:]
            else:
                # Calculate target end for this chunk
                target_end = min(current_pos + target_size, len(content))
                
                # Find clean boundary
                split_pos = self._find_boundary(content, target_end, boundary_type, forward=True)
                
                if split_pos == -1 or split_pos <= current_pos:
                    split_pos = target_end
                
                chunk = content[current_pos:split_pos]
                
                # Ensure we don't exceed max_size
                if len(chunk) > max_size:
                    # Force split at max_size boundary
                    split_pos = self._find_boundary(content, current_pos + max_size, boundary_type, forward=True)
                    if split_pos > current_pos:
                        chunk = content[current_pos:split_pos]
                    else:
                        chunk = content[current_pos:current_pos + max_size]
                        split_pos = current_pos + max_size
                
                current_pos = split_pos
            
            # Add overlap for context (except first chunk)
            if overlap > 0 and chunks and len(chunk) > overlap:
                chunk = self._add_overlap(chunks[-1], chunk, overlap)
            
            chunks.append(chunk)
            
            # Adjust position for overlap
            if overlap > 0 and not is_last:
                current_pos = max(current_pos - overlap, current_pos)
        
        return chunks
    
    def _split_by_file_count(self, content: str, max_files: int, boundary_type: BoundaryType, overlap: int) -> List[str]:
        """Split into exactly N files, balancing content."""
        if max_files <= 1:
            return [content]
        
        target_size = len(content) // max_files
        return self._split_by_size(content, target_size, boundary_type, overlap)
    
    def _split_by_size(self, content: str, max_bytes: int, boundary_type: BoundaryType, overlap: int) -> List[str]:
        """Split content ensuring each chunk is under max_bytes."""
        chunks = []
        current_pos = 0
        content_len = len(content)
        
        while current_pos < content_len:
            target_end = min(current_pos + max_bytes, content_len)
            
            if target_end >= content_len:
                chunks.append(content[current_pos:])
                break
            
            split_pos = self._find_boundary(content, target_end, boundary_type, forward=True)
            
            if split_pos == -1 or split_pos <= current_pos:
                split_pos = target_end
            
            chunk = content[current_pos:split_pos]
            
            if overlap > 0 and chunks and len(chunk) > overlap:
                chunk = self._add_overlap(chunks[-1], chunk, overlap)
            
            chunks.append(chunk)
            current_pos = split_pos
            
            if overlap > 0:
                current_pos = max(current_pos - overlap, current_pos)
        
        return chunks
    
    def _split_by_sections(self, content: str, boundary_type: BoundaryType, overlap: int) -> List[str]:
        """Split at logical sections."""
        if boundary_type == BoundaryType.FUNCTION:
            return self._split_by_functions(content, overlap)
        elif boundary_type == BoundaryType.CLASS:
            return self._split_by_classes(content, overlap)
        elif boundary_type == BoundaryType.MARKDOWN_HEADING:
            return self._split_by_headings(content, overlap)
        else:
            return self._split_by_paragraphs(content, overlap)
    
    def _split_by_functions(self, content: str, overlap: int) -> List[str]:
        """Split at function boundaries."""
        function_pattern = r'(\n\s*(?:def|function|async def|func)\s+\w+\s*\([^)]*\)\s*[:{][\s\S]*?)(?=\n\s*(?:def|function|async def|func|class|type)\s+\w+|\Z)'
        
        matches = list(re.finditer(function_pattern, content, re.MULTILINE))
        
        if not matches or len(matches) <= 1:
            return [content]
        
        chunks = []
        for i, match in enumerate(matches):
            chunk = match.group(1)
            if overlap > 0 and i > 0 and len(chunk) > overlap:
                chunk = self._add_overlap(matches[i-1].group(1), chunk, overlap)
            chunks.append(chunk)
        
        return chunks
    
    def _split_by_classes(self, content: str, overlap: int) -> List[str]:
        """Split at class boundaries."""
        class_pattern = r'(\n\s*(?:class|interface|trait|type)\s+\w+[\s\S]*?)(?=\n\s*(?:class|interface|trait|type)\s+\w+|\Z)'
        
        matches = list(re.finditer(class_pattern, content, re.MULTILINE))
        
        if not matches or len(matches) <= 1:
            return [content]
        
        chunks = []
        for i, match in enumerate(matches):
            chunk = match.group(1)
            if overlap > 0 and i > 0 and len(chunk) > overlap:
                chunk = self._add_overlap(matches[i-1].group(1), chunk, overlap)
            chunks.append(chunk)
        
        return chunks
    
    def _split_by_headings(self, content: str, overlap: int) -> List[str]:
        """Split at markdown headings."""
        heading_pattern = r'(\n#{1,6}\s+[^\n]+[\s\S]*?)(?=\n#{1,6}\s+|\Z)'
        
        matches = list(re.finditer(heading_pattern, content, re.MULTILINE))
        
        if not matches or len(matches) <= 1:
            return [content]
        
        chunks = []
        for i, match in enumerate(matches):
            chunk = match.group(1)
            if overlap > 0 and i > 0 and len(chunk) > overlap:
                chunk = self._add_overlap(matches[i-1].group(1), chunk, overlap)
            chunks.append(chunk)
        
        return chunks
    
    def _split_by_paragraphs(self, content: str, overlap: int) -> List[str]:
        """Split at paragraph boundaries."""
        paragraphs = re.split(r'\n\s*\n', content)
        
        if len(paragraphs) <= 1:
            return [content]
        
        chunks = []
        current_chunk = ""
        target_size = 10000
        
        for para in paragraphs:
            if len(current_chunk) + len(para) > target_size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks if chunks else [content]
    
    def _split_by_characters(self, content: str, max_chars: int, boundary_type: BoundaryType, overlap: int) -> List[str]:
        """Split by exact character count with boundary awareness."""
        chunks = []
        current_pos = 0
        
        while current_pos < len(content):
            chunk_end = min(current_pos + max_chars, len(content))
            
            if chunk_end < len(content):
                split_pos = self._find_boundary(content, chunk_end, boundary_type, forward=True)
                if split_pos > current_pos:
                    chunk_end = split_pos
            
            chunk = content[current_pos:chunk_end]
            
            if overlap > 0 and chunks and len(chunk) > overlap:
                chunk = self._add_overlap(chunks[-1], chunk, overlap)
            
            chunks.append(chunk)
            current_pos = chunk_end
            
            if overlap > 0:
                current_pos = max(current_pos - overlap, current_pos)
        
        return chunks
    
    def _split_balanced(self, content: str, boundary_type: BoundaryType, overlap: int) -> List[str]:
        """Balanced splitting that tries to create equal-sized chunks."""
        sections = self._detect_natural_sections(content)
        
        if len(sections) <= 1:
            return self._split_by_size(content, 50000, boundary_type, overlap)
        
        chunks = []
        current_chunk = ""
        target_size = len(content) // 3
        
        for section in sections:
            if len(current_chunk) + len(section) > target_size * 1.5:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = section
            else:
                if current_chunk:
                    current_chunk += "\n\n" + section
                else:
                    current_chunk = section
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _detect_natural_sections(self, content: str) -> List[str]:
        """Detect natural section boundaries in content."""
        sections = []
        
        heading_matches = list(re.finditer(r'\n#{1,6}\s+[^\n]+', content))
        
        if len(heading_matches) >= 2:
            for i, match in enumerate(heading_matches):
                start = match.start()
                end = heading_matches[i + 1].start() if i + 1 < len(heading_matches) else len(content)
                sections.append(content[start:end])
        else:
            sections = re.split(r'\n\s*\n', content)
        
        return sections if sections else [content]
    
    def _find_boundary(self, content: str, position: int, boundary_type: BoundaryType, forward: bool = True) -> int:
        """Find the nearest clean boundary near the given position."""
        if position <= 0 or position >= len(content):
            return position
        
        search_range = 2000
        start = max(0, position - search_range)
        end = min(len(content), position + search_range)
        search_content = content[start:end]
        
        if boundary_type == BoundaryType.WORD:
            pattern = r'\s+'
        elif boundary_type == BoundaryType.SENTENCE:
            pattern = r'[.!?]\s+(?=[A-Z])'
        elif boundary_type == BoundaryType.PARAGRAPH:
            pattern = r'\n\s*\n'
        elif boundary_type == BoundaryType.FUNCTION:
            pattern = r'\n(def|function|async def|func)\s+\w+'
        elif boundary_type == BoundaryType.CLASS:
            pattern = r'\n(class|interface|trait|type)\s+\w+'
        elif boundary_type == BoundaryType.MARKDOWN_HEADING:
            pattern = r'\n#{1,6}\s+'
        else:
            pattern = r'\s+'
        
        matches = list(re.finditer(pattern, search_content))
        
        if not matches:
            return position
        
        original_in_search = position - start
        closest_match = None
        min_distance = float('inf')
        
        for match in matches:
            bound_pos = match.end() if forward else match.start()
            distance = abs(bound_pos - original_in_search)
            if distance < min_distance:
                min_distance = distance
                closest_match = bound_pos
        
        if closest_match is not None:
            return start + closest_match
        
        return position
    
    def _add_overlap(self, prev_chunk: str, current_chunk: str, overlap_chars: int) -> str:
        """Add overlap from previous chunk for context preservation."""
        if len(prev_chunk) <= overlap_chars:
            overlap_text = prev_chunk
        else:
            cut_point = len(prev_chunk) - overlap_chars
            cut_point = self._find_boundary(prev_chunk, cut_point, BoundaryType.SENTENCE, forward=True)
            overlap_text = prev_chunk[cut_point:]
        
        return f"\n{'=' * 50}\n[📋 CONTEXT FROM PREVIOUS SECTION - AI NOTE: This helps maintain continuity]\n{'=' * 50}\n{overlap_text}\n{'=' * 50}\n[📋 END CONTEXT]\n{'=' * 50}\n\n{current_chunk}"
    
    def validate_split(self, chunks: List[str]) -> Dict[str, Any]:
        """Validate split results and provide statistics."""
        if not chunks:
            return {'num_chunks': 0, 'total_size': 0, 'avg_size': 0, 'min_size': 0, 'max_size': 0, 'chunks_sizes': [], 'is_balanced': True}
        
        total_original = sum(len(chunk) for chunk in chunks)
        
        stats = {
            'num_chunks': len(chunks),
            'total_size': total_original,
            'avg_size': total_original // len(chunks),
            'min_size': min(len(c) for c in chunks),
            'max_size': max(len(c) for c in chunks),
            'chunks_sizes': [len(c) for c in chunks],
            'is_balanced': len(set(len(c) for c in chunks)) <= 3
        }
        
        return stats
    
    def save_split_files(self, chunks: List[str], output_dir: str, base_name: str = "split_part", extension: str = "txt") -> List[str]:
        """Save split chunks to files."""
        os.makedirs(output_dir, exist_ok=True)
        saved_paths = []
        
        for i, chunk in enumerate(chunks, 1):
            filename = f"{base_name}_{i:03d}.{extension}"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(chunk)
            
            saved_paths.append(filepath)
            file_size = len(chunk.encode('utf-8'))
            size_mb = file_size / (1024 * 1024)
            print(f"  ✅ Saved: {filename} ({size_mb:.2f} MB, {len(chunk):,} chars)")
        
        return saved_paths