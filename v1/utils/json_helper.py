"""
JSON Helper module for Tokopedia Sentiment Analysis
Provides robust JSON handling functions to prevent parsing errors
"""

import json
import os
import re
import traceback
from datetime import datetime

def safe_load_json(file_path):
    """
    Safely load a JSON file with error handling and recovery attempts
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        dict: The loaded JSON data or a default dictionary if loading fails
        bool: Success status
        str: Error message if any
    """
    if not os.path.exists(file_path):
        return {}, False, f"File not found: {file_path}"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, True, None
    except json.JSONDecodeError as e:
        # First attempt: Try to recover the file by fixing common JSON syntax errors
        error_msg = f"JSON decode error: {str(e)}"
        recovered_data, success = try_recover_json(file_path, e)
        
        if success:
            return recovered_data, True, f"JSON was automatically fixed: {str(e)}"
        else:
            return {}, False, error_msg
    except Exception as e:
        error_msg = f"Error reading JSON file: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        return {}, False, error_msg

def try_recover_json(file_path, error):
    """
    Attempt to recover a corrupted JSON file
    
    Args:
        file_path: Path to the corrupted JSON file
        error: The JSON decode error
        
    Returns:
        dict: Recovered data if successful
        bool: Success status
    """
    try:
        # Extract error position information
        error_msg = str(error)
        error_line = 0
        error_col = 0
        error_char = 0
        
        # Parse error message to get position info
        if "line" in error_msg and "column" in error_msg:
            line_match = re.search(r'line (\d+)', error_msg)
            col_match = re.search(r'column (\d+)', error_msg)
            char_match = re.search(r'char (\d+)', error_msg)
            
            if line_match:
                error_line = int(line_match.group(1))
            if col_match:
                error_col = int(col_match.group(1))
            if char_match:
                error_char = int(char_match.group(1))
        
        print(f"🔍 JSON error at line {error_line}, column {error_col}, char {error_char}")
        
        # Create a backup of the corrupted file
        backup_path = f"{file_path}.corrupted.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        with open(file_path, 'r', encoding='utf-8') as src:
            content = src.read()
            
        # Save backup
        with open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(content)
        
        print(f"✅ Backup saved to: {backup_path}")
        
        # Special handling for line 32 column 26 error (common in your files)
        if error_line == 32 and error_col == 26:
            # Get the specific area around the error
            lines = content.split('\n')
            
            if error_line <= len(lines):
                problem_line = lines[error_line-1]
                print(f"🔍 Problem line: {problem_line}")
                
                # Check for typical patterns near char 994
                content_before_error = content[:error_char]
                content_after_error = content[error_char:]
                
                # Look for incomplete JSON tokens
                if content_before_error.endswith('"'):
                    # Missing closing quote - add it
                    fixed_content = content_before_error + content_after_error.replace('", "', '", "', 1)
                elif '"": ' in problem_line:
                    # Empty key with syntax error
                    fixed_content = content.replace('"": ', '"empty": ', 1)
                elif ',"' in problem_line and not problem_line.strip().endswith(',') and not problem_line.strip().endswith('{'):
                    # Missing value after key - add null
                    fixed_content = content.replace(',"', ',"": null,"', 1)
                else:
                    # Try generic repair around the error point
                    fixed_content = content[:error_char] + ' null ' + content[error_char:]
                
                print("🔧 Applied special fix for line 32 column 26 error")
            else:
                fixed_content = content
        else:
            # Try general fixes
            fixed_content = content
        
        # Fix 1: Missing comma between objects
        fixed_content = fixed_content.replace('""', '","')
        fixed_content = fixed_content.replace('}{', '},{')
        
        # Fix 2: Trailing comma in arrays or objects
        fixed_content = fixed_content.replace(',]', ']')
        fixed_content = fixed_content.replace(',}', '}')
        
        # Fix 3: Unbalanced quotes in strings
        lines = fixed_content.split('\n')
        for i, line in enumerate(lines):
            if '"' in line and line.count('"') % 2 != 0:
                # This line has unbalanced quotes, try to fix it
                if i > 0 and i < len(lines) - 1:
                    prev_line = lines[i-1]
                    next_line = lines[i+1]
                    
                    # If the line before or after has a dangling quote, combine them
                    if prev_line.count('"') % 2 != 0:
                        lines[i-1] = prev_line + line
                        lines[i] = ""
                    elif next_line.count('"') % 2 != 0:
                        lines[i] = line + next_line
                        lines[i+1] = ""
                    else:
                        # Try to fix the line by adding a closing quote
                        if line.strip().endswith(':'):
                            lines[i] = line + ' ""'
                        elif line.strip().endswith(','):
                            lines[i] = line[:-1] + '",'
                        else:
                            lines[i] = line + '"'
        
        fixed_content = '\n'.join([l for l in lines if l])
        
        # Fix 4: Missing values (common in your files)
        fixed_content = re.sub(r'": *(,|\})', '": null\\1', fixed_content)
        
        # Fix 5: Truncated content - add closing braces if needed
        open_braces = fixed_content.count('{')
        close_braces = fixed_content.count('}')
        if open_braces > close_braces:
            fixed_content += "}" * (open_braces - close_braces)
        
        open_brackets = fixed_content.count('[')
        close_brackets = fixed_content.count(']')
        if open_brackets > close_brackets:
            fixed_content += "]" * (open_brackets - close_brackets)
        
        # Try to parse the fixed content
        try:
            recovered_data = json.loads(fixed_content)
            
            # If successful, save the fixed content back
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(recovered_data, f, ensure_ascii=False, indent=2)
                
            print(f"✅ Successfully recovered corrupted JSON file: {file_path}")
            return recovered_data, True
            
        except json.JSONDecodeError as e2:
            # Second attempt with more aggressive fixes
            print(f"🔄 First repair attempt failed: {str(e2)}")
            
            try:
                # Try a more aggressive approach - manually construct a minimal valid JSON
                minimal_json = extract_valid_json_parts(fixed_content)
                if minimal_json:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(minimal_json, f, ensure_ascii=False, indent=2)
                    print(f"✅ Recovered with minimal valid JSON structure")
                    return minimal_json, True
            except Exception as e3:
                print(f"❌ Second repair attempt failed: {str(e3)}")
                
            return {}, False
            
    except Exception as e:
        print(f"❌ Failed to recover JSON: {str(e)}")
        return {}, False

def extract_valid_json_parts(content):
    """Extract valid parts of a JSON string and create a minimal valid structure"""
    try:
        # Create a minimal valid structure
        result = {
            "data": [],
            "metrics": {
                "total_reviews": 0,
                "positive_reviews": 0,
                "negative_reviews": 0,
                "accuracy": 0.0
            },
            "summary": {
                "total_reviews": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0
            },
            "original_file": "",
            "timestamp": datetime.now().isoformat(),
            "status": "draft"
        }
        
        # Try to extract fields using regex
        original_match = re.search(r'"original_file"\s*:\s*"([^"]+)"', content)
        if original_match:
            result["original_file"] = original_match.group(1)
            
        # Try to extract metrics
        total_match = re.search(r'"total_reviews"\s*:\s*(\d+)', content)
        if total_match:
            result["metrics"]["total_reviews"] = int(total_match.group(1))
            result["summary"]["total_reviews"] = int(total_match.group(1))
            
        pos_match = re.search(r'"positive_reviews"\s*:\s*(\d+)', content)
        if pos_match:
            result["metrics"]["positive_reviews"] = int(pos_match.group(1))
            result["summary"]["positive_count"] = int(pos_match.group(1))
            
        neg_match = re.search(r'"negative_reviews"\s*:\s*(\d+)', content)
        if neg_match:
            result["metrics"]["negative_reviews"] = int(neg_match.group(1))
            result["summary"]["negative_count"] = int(neg_match.group(1))
        
        # Extract any data array items that might be valid
        data_matches = re.findall(r'\{[^{}]*"Ulasan"\s*:[^{}]*\}', content)
        for i, match in enumerate(data_matches[:100]):  # Limit to first 100 to avoid excessive size
            try:
                item = json.loads(match)
                result["data"].append(item)
            except:
                continue
                
        return result
    except Exception as e:
        print(f"❌ Error extracting valid JSON parts: {str(e)}")
        return None
