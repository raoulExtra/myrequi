"""
Filesystem Extraction Module
Implements functionality to extract specific sections from configuration files
based on inclusion and exclusion patterns.
"""

import os
import re
from typing import List, Optional


def extract_sections(config_file_path: str, 
                    include_patterns: List[str], 
                    exclude_patterns: List[str]) -> str:
    """
    Extract specific sections from a configuration file based on inclusion and exclusion patterns.
    
    Args:
        config_file_path (str): Path to the configuration file
        include_patterns (List[str]): List of patterns to include (empty = include all)
        exclude_patterns (List[str]): List of patterns to exclude (empty = exclude none)
    
    Returns:
        str: Extracted content from the configuration file
    """
    try:
        # Read the entire file content
        with open(config_file_path, 'r') as file:
            content = file.read()
        
        # If no patterns specified, return all content
        if not include_patterns and not exclude_patterns:
            return content
        
        # Split content into lines for pattern matching
        lines = content.splitlines()
        extracted_lines = []
        current_section = ""
        
        for line in lines:
            # Check if this line starts a new section
            # Supports [section] and # header markdown styles
            section_match = re.match(r'^\[(.*)\]|^(#+)\s*(.*)', line.strip())
            if section_match:
                current_section = section_match.group(1) or section_match.group(3)
            
            # Determine if this line should be included
            include_line = _should_include_line(line, current_section, include_patterns, exclude_patterns)
            
            if include_line:
                extracted_lines.append(line)
        
        return '\n'.join(extracted_lines)
    
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_file_path}")
    except Exception as e:
        raise Exception(f"Error extracting sections from {config_file_path}: {str(e)}")


def extract_sections_to_file(config_file_path: str,
                           include_patterns: List[str],
                           exclude_patterns: List[str],
                           output_suffix: str = '_extracted') -> str:
    """
    Extract sections and write to a new file with `_extracted` suffix.

    Args:
        config_file_path (str): Path to the configuration file
        include_patterns (List[str]): Patterns to include
        exclude_patterns (List[str]): Patterns to exclude
        output_suffix (str): Suffix inserted before file extension

    Returns:
        str: Path to the generated output file
    """
    extracted = extract_sections(config_file_path, include_patterns, exclude_patterns)

    root, ext = os.path.splitext(config_file_path)
    output_path = f"{root}{output_suffix}{ext}"

    with open(output_path, 'w') as file:
        file.write(extracted)

    return output_path


def _should_include_line(line: str, 
                       current_section: str, 
                       include_patterns: List[str], 
                       exclude_patterns: List[str]) -> bool:
    """
    Determine if a line should be included based on patterns.
    
    Args:
        line (str): The line to check
        current_section (str): The current section name
        include_patterns (List[str]): List of inclusion patterns
        exclude_patterns (List[str]): List of exclusion patterns
    
    Returns:
        bool: True if the line should be included
    """
    # If no inclusion patterns, we include by default
    include_by_default = not include_patterns
    
    # Check if line matches any inclusion pattern
    if include_patterns:
        include_match = any(pattern.lower() in line.lower() or 
                          (current_section and pattern.lower() in current_section.lower())
                          for pattern in include_patterns)
    else:
        include_match = True
    
    # Check if line matches any exclusion pattern
    exclude_match = any(pattern.lower() in line.lower() or 
                      (current_section and pattern.lower() in current_section.lower())
                      for pattern in exclude_patterns)
    
    # Include if:
    # 1. No inclusion patterns specified (include by default) AND not excluded
    # 2. Has inclusion pattern match AND not excluded
    if include_by_default:
        return not exclude_match
    else:
        return include_match and not exclude_match


def extract_sections_simple(config_file_path: str, 
                           include_patterns: List[str], 
                           exclude_patterns: List[str]) -> str:
    """
    Simple version of section extraction for basic configuration handling.
    
    Args:
        config_file_path (str): Path to the configuration file
        include_patterns (List[str]): List of patterns to include
        exclude_patterns (List[str]): List of patterns to exclude
    
    Returns:
        str: Extracted content from the configuration file
    """
    try:
        # Read the entire file content
        with open(config_file_path, 'r') as file:
            lines = file.readlines()
        
        # If no patterns specified, return all content
        if not include_patterns and not exclude_patterns:
            return ''.join(lines)
        
        # Track which sections to include
        sections_to_include = set()
        sections_to_exclude = set()
        
        # First pass: determine which sections to include/exclude based on patterns
        for line in lines:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                section_name = line[1:-1]  # Remove brackets
                
                if include_patterns:
                    if any(pattern.lower() in section_name.lower() for pattern in include_patterns):
                        sections_to_include.add(section_name)
                else:
                    sections_to_include.add(section_name)
                
                if exclude_patterns:
                    if any(pattern.lower() in section_name.lower() for pattern in exclude_patterns):
                        sections_to_exclude.add(section_name)
        
        # Filter out excluded sections
        if sections_to_include and sections_to_exclude:
            sections_to_include = sections_to_include - sections_to_exclude
        
        # Second pass: build result with only included sections
        result_lines = []
        current_section = ""
        in_included_section = False
        
        for line in lines:
            line = line.rstrip('\n')
            
            # Check for section headers — supports [section] and # header markdown styles
            m = re.match(r'^\[(.*)\]|^(#+)\s*(.*)', line)
            if m:
                section_name = m.group(1) or m.group(3)
                if section_name in sections_to_include:
                    current_section = section_name
                    in_included_section = True
                    result_lines.append(line)
                else:
                    current_section = ""
                    in_included_section = False
            elif in_included_section:
                result_lines.append(line)
            elif not line.strip():  # Empty lines
                result_lines.append(line)
            # Do not include lines from non-included sections
        
        return '\n'.join(result_lines).rstrip('\n') + '\n'
    
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_file_path}")
    except Exception as e:
        raise Exception(f"Error extracting sections from {config_file_path}: {str(e)}")


# Backwards compatible alias kept; both implementations now support markdown # headers


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2:
        config_path = sys.argv[1]
        includes = sys.argv[2].split(',') if len(sys.argv) > 2 else []
        excludes = sys.argv[3].split(',') if len(sys.argv) > 3 else []
        out = extract_sections_to_file(config_path, includes, excludes)
        print(f"Extracted to: {out}")
    else:
        print("Usage: python filesystem_extraction.py <file> [include_patterns] [exclude_patterns]")