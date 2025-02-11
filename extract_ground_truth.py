import json
import os

def filter_node(node):
    # Recursively filter node: if a dict contains an 'id' with "s" in it, skip it.
    if isinstance(node, dict):
        if 'id' in node and ('s' in node['id'].lower()):
            return None
        new_dict = {}
        for key, value in node.items():
            filtered = filter_node(value)
            # if filtering a list or dict returns a falsey (None), we still want to include keys like title/text
            if filtered is not None:
                new_dict[key] = filtered
        return new_dict
    elif isinstance(node, list):
        new_list = []
        for item in node:
            filtered_item = filter_node(item)
            if filtered_item is not None:
                new_list.append(filtered_item)
        return new_list
    else:
        return node

def build_tree(node):
    # Recursively build a tree with only "title" (and optional "children")
    if isinstance(node, dict):
        if "title" in node:
            new_node = {"title": node["title"]}
            if "content" in node and isinstance(node["content"], list):
                children = []
                for child in node["content"]:
                    child_tree = build_tree(child)
                    if child_tree:
                        if isinstance(child_tree, list):
                            children.extend(child_tree)
                        else:
                            children.append(child_tree)
                if children:
                    new_node["children"] = children
            return new_node
        else:
            if "content" in node and isinstance(node["content"], list):
                children = []
                for child in node["content"]:
                    child_tree = build_tree(child)
                    if child_tree:
                        if isinstance(child_tree, list):
                            children.extend(child_tree)
                        else:
                            children.append(child_tree)
                if children:
                    return {"children": children}
            return None
    elif isinstance(node, list):
        trees = []
        for item in node:
            tree = build_tree(item)
            if tree:
                if isinstance(tree, list):
                    trees.extend(tree)
                else:
                    trees.append(tree)
        return trees if trees else None
    return None

def build_markdown(node, level=1):
    """
    Recursively builds a markdown text from the JSON content.
    Only includes 'title' and text from 'sentences', ignoring references.
    """
    md = ""
    if isinstance(node, dict):
        if "title" in node:
            md += ("#" * level) + " " + node["title"] + "\n\n"
        if "sentences" in node and isinstance(node["sentences"], list):
            for sentence in node["sentences"]:
                if "text" in sentence:
                    md += sentence["text"].strip() + "\n\n"
        if "content" in node and isinstance(node["content"], list):
            for child in node["content"]:
                md += build_markdown(child, level+1)
    elif isinstance(node, list):
        for item in node:
            md += build_markdown(item, level)
    return md

def extractDirectoryTree(input_file_path):
    # Read original JSON file
    with open(input_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filter JSON tree based on node "id"
    filtered_data = filter_node(data)

    # Build tree containing only the layer structure and titles
    tree_structure = build_tree(filtered_data)

    # Validate that tree_structure is valid JSON by serializing and deserializing it
    try:
        s = json.dumps(tree_structure)
        valid_tree = json.loads(s)
    except Exception as e:
        raise ValueError("Invalid JSON structure: " + str(e))
    
    # Return the valid JSON structure without saving to a file
    return valid_tree

def extractMarkdownContent(input_file_path):
    # Read original JSON file
    with open(input_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Build markdown text from JSON structure
    md_text = build_markdown(data)
    
    # Return markdown text instead of saving to a file
    return md_text

def extract_markdown_sections(md_text):
    """
    Extract markdown sections based on header lines.
    遇到新的标题（以#开头）则开始新的 section，
    返回一个包含各 section 的列表，每个 section 为一个字符串。
    """
    sections = []
    current_section = []
    for line in md_text.splitlines():
        if line.strip().startswith("#"):
            if current_section:
                sections.append("\n".join(current_section).strip())
                current_section = []
        current_section.append(line)
    if current_section:
        sections.append("\n".join(current_section).strip())
    return sections

if __name__ == "__main__":
    input_path = "/Users/logic/Documents/CodeSpace/CriticSearch/final_wiki/2024_European_floods.json"
    valid_tree = extractDirectoryTree(input_path)
    print(f"Extracted tree structure: \n{valid_tree}")
    
    # New call to extractMarkdownContent: print markdown text directly
    md_text = extractMarkdownContent(input_path)
    print(f"Markdown content: \n{md_text}")