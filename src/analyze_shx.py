#!/usr/bin/env python3

def main():
    try:
        with open('shx.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"File size: {len(content)} characters")
        print(f"Number of lines: {len(content.splitlines())}")
        
        # Just show the first 100 lines with line numbers
        print("\n=== FIRST 100 LINES ===")
        lines = content.splitlines()
        for i, line in enumerate(lines[:100], 1):
            print(f"{i:3}: {line}")
        
        if len(lines) > 100:
            print(f"... and {len(lines) - 100} more lines")
        
        # Find and show the politics section
        print("\n=== POLITICS SECTION ===")
        politics_start = content.find("politics={")
        if politics_start != -1:
            # Find the end of politics section by counting braces
            pos = politics_start + len("politics={")
            brace_count = 1
            
            while pos < len(content) and brace_count > 0:
                if content[pos] == '{':
                    brace_count += 1
                elif content[pos] == '}':
                    brace_count -= 1
                pos += 1
            
            politics_section = content[politics_start:pos]
            print(politics_section)
        else:
            print("Politics section not found!")
        
        # Show key-value pairs at the top level
        print("\n=== TOP-LEVEL FIELDS ===")
        for line in lines:
            stripped = line.strip()
            if '=' in stripped and not stripped.endswith('={') and not stripped.endswith('='):
                if stripped.count('=') == 1:  # Simple key=value
                    key, value = stripped.split('=', 1)
                    if len(key) < 30:  # Skip very long keys
                        print(f"{key}: {value}")
        
    except FileNotFoundError:
        print("Error: shx.txt not found!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()