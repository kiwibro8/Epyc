import tokenize
import io

def remove_comments(source):
    io_obj = io.StringIO(source)
    out = []
    last_lineno = -1
    last_col = 0
    
    for tok in tokenize.generate_tokens(io_obj.readline):
        token_type = tok[0]
        token_string = tok[1]
        start_line, start_col = tok[2]
        end_line, end_col = tok[3]
        
        if start_line > last_lineno:
            last_col = 0
            
        if start_col > last_col:
            # We only append space if we are not skipping a comment.
            # But wait, if we skipped a comment, last_col is NOT updated to end_col?
            # Actually, the simplest logic is to update last_col unconditionally.
            out.append(" " * (start_col - last_col))
            
        if token_type == tokenize.COMMENT:
            # For comments, we don't append the token_string.
            # But we must update last_col and last_lineno to not mess up subsequent tokens.
            pass
        else:
            out.append(token_string)
            
        last_col = end_col
        last_lineno = end_line
        
    return "".join(out)

with open('main.py', 'r', encoding='utf-8') as f:
    source = f.read()

# Also remove empty lines that contain only whitespace after removing comments
lines = remove_comments(source).splitlines()
cleaned_lines = []
for line in lines:
    if line.strip() == "" and not source.splitlines()[len(cleaned_lines)].strip() == "":
        # This means the line became empty because we stripped a comment.
        # Wait, matching lines is hard. Let's just output the exact lines, 
        # but if a line is completely empty and wasn't before, maybe we skip it?
        # Actually it's fine to leave empty lines. Let's just strip trailing whitespace.
        cleaned_lines.append(line.rstrip())
    else:
        cleaned_lines.append(line.rstrip())

with open('main.py', 'w', encoding='utf-8') as f:
    f.write("\n".join(cleaned_lines) + "\n")
